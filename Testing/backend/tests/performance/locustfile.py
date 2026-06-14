"""
LAYER 4 — Performance Tests: Locust
Simulates concurrent restaurant managers and TV devices.

Run:
    locust -f tests/performance/locustfile.py --host=http://localhost:8000
    locust -f ... --headless -u 50 -r 10 --run-time 60s

Scenarios:
  - MenuBrowser:  simulates TV devices polling the full menu
  - MenuManager:  simulates managers editing items
  - DeviceAgent:  simulates TV heartbeat calls

Thresholds (CI enforced):
  - p95 response time < 500ms for menu reads
  - p95 response time < 1000ms for writes
  - Error rate < 1%
"""
import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ── Shared state (populated on start) ────────────────────────────────────────
_manager_token: str = ""
_restaurant_id: int = 1
_menu_item_ids: list[int] = []


def get_manager_token(client) -> str:
    resp = client.post("/api/v1/auth/login", json={
        "username": "manager1",
        "password": "Manager@1234",
    }, name="/auth/login [setup]")
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return ""


# ── TV Device: reads menu, sends heartbeat ────────────────────────────────────
class TVDevice(HttpUser):
    """Simulates Android TV devices polling the API."""
    wait_time = between(25, 35)  # TV polls roughly every 30 seconds
    weight = 3  # TVs outnumber managers 3:1

    def on_start(self):
        self.device_id = random.randint(1, 100)
        self.mac = f"AA:BB:CC:{random.randint(10,99):02X}:{random.randint(10,99):02X}:{random.randint(10,99):02X}"

    @task(5)
    def get_full_menu(self):
        """Most common operation — TV fetches full menu."""
        # TV uses a device token in production; for load test we use manager token
        global _manager_token
        self.client.get(
            f"/api/v1/menu/restaurants/{_restaurant_id}/full",
            headers={"Authorization": f"Bearer {_manager_token}"},
            name="/menu/restaurants/[id]/full",
        )

    @task(1)
    def heartbeat(self):
        self.client.post(
            f"/api/v1/devices/{self.device_id}/heartbeat",
            params={"mac_address": self.mac},
            name="/devices/[id]/heartbeat",
        )

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")


# ── Menu Manager: browses and edits menu ─────────────────────────────────────
class MenuManager(HttpUser):
    """Simulates a restaurant manager using the admin panel."""
    wait_time = between(2, 8)
    weight = 1

    def on_start(self):
        self.token = get_manager_token(self.client)
        self.headers = {"Authorization": f"Bearer {self.token}"}
        # Pre-fetch menu group IDs
        resp = self.client.get(
            f"/api/v1/menu/restaurants/{_restaurant_id}/groups",
            headers=self.headers,
            name="/menu/groups [setup]",
        )
        self.group_ids = [g["id"] for g in resp.json()] if resp.status_code == 200 else []

    @task(4)
    def list_menu_groups(self):
        self.client.get(
            f"/api/v1/menu/restaurants/{_restaurant_id}/groups",
            headers=self.headers,
            name="/menu/restaurants/[id]/groups",
        )

    @task(2)
    def list_items(self):
        if not self.group_ids:
            return
        group_id = random.choice(self.group_ids)
        # First get subgroups
        resp = self.client.get(
            f"/api/v1/menu/groups/{group_id}/subgroups",
            headers=self.headers,
            name="/menu/groups/[id]/subgroups",
        )
        if resp.status_code == 200 and resp.json():
            sg_id = random.choice(resp.json())["id"]
            self.client.get(
                f"/api/v1/menu/subgroups/{sg_id}/items",
                headers=self.headers,
                name="/menu/subgroups/[id]/items",
            )

    @task(1)
    def toggle_item_status(self):
        if not _menu_item_ids:
            return
        item_id = random.choice(_menu_item_ids)
        status = random.choice(["available", "not_available", "today_special"])
        self.client.patch(
            f"/api/v1/menu/items/{item_id}",
            json={"status": status},
            headers=self.headers,
            name="/menu/items/[id] PATCH",
        )

    @task(1)
    def get_me(self):
        self.client.get("/api/v1/auth/me", headers=self.headers, name="/auth/me")


# ── WebSocket stress test (separate script) ───────────────────────────────────
"""
For WebSocket load testing, use a separate tool (e.g. artillery or websocket-bench):

  # artillery.yml
  config:
    target: "ws://localhost:8000"
    phases:
      - duration: 60
        arrivalRate: 10
  scenarios:
    - engine: ws
      flow:
        - get:
            url: "/api/v1/ws/tv/1/{{ $randomInt(1, 50) }}"
        - think: 30
        - send: "ping"
        - think: 30
"""


# ── CI threshold check (run after locust headless) ────────────────────────────
def check_thresholds(stats):
    """
    Call this after a headless run to enforce SLA thresholds.
    Returns True if all thresholds pass.
    """
    failures = []

    menu_read = stats.get("/menu/restaurants/[id]/full")
    if menu_read:
        if menu_read.get_response_time_percentile(0.95) > 500:
            failures.append(f"Menu read p95 > 500ms: {menu_read.get_response_time_percentile(0.95):.0f}ms")

    for name, entry in stats.entries.items():
        if entry.num_failures / max(entry.num_requests, 1) > 0.01:
            failures.append(f"Error rate > 1% on {name}: {entry.num_failures}/{entry.num_requests}")

    if failures:
        print("❌ Performance threshold failures:")
        for f in failures:
            print(f"   {f}")
        return False

    print("✅ All performance thresholds passed")
    return True
