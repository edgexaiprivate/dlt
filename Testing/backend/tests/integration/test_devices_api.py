"""
LAYER 2 — Integration Tests: Device API + Health
Tests device registration, status, heartbeat, and the /health endpoint.
"""
import pytest


class TestHealthEndpoint:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "env" in data

    async def test_health_is_public(self, client):
        """Health endpoint must be accessible without auth for load balancer checks."""
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_docs_reachable(self, client):
        resp = await client.get("/docs")
        assert resp.status_code == 200


class TestDeviceAPI:
    async def test_list_devices_authenticated(self, client, manager_headers, device):
        resp = await client.get("/api/v1/devices", headers=manager_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Main Hall TV"

    async def test_list_devices_unauthenticated(self, client):
        resp = await client.get("/api/v1/devices")
        assert resp.status_code == 403

    async def test_register_device(self, client, manager_headers, branch):
        resp = await client.post("/api/v1/devices", headers=manager_headers, json={
            "branch_id": branch.id,
            "name": "Counter Display",
            "display_number": 2,
            "mac_address": "11:22:33:44:55:66",
            "screen_size_inch": 43,
            "theme_id": 1,
            "active_session": "all_day",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Counter Display"
        assert data["mac_address"] == "11:22:33:44:55:66"
        assert data["status"] == "unregistered"  # default until heartbeat

    async def test_register_duplicate_mac_rejected(self, client, manager_headers, branch, device):
        resp = await client.post("/api/v1/devices", headers=manager_headers, json={
            "branch_id": branch.id,
            "name": "Duplicate",
            "display_number": 5,
            "mac_address": "AA:BB:CC:DD:EE:FF",  # same as fixture device
        })
        assert resp.status_code == 409

    async def test_register_invalid_mac_rejected(self, client, manager_headers, branch):
        resp = await client.post("/api/v1/devices", headers=manager_headers, json={
            "branch_id": branch.id,
            "name": "Bad MAC",
            "display_number": 3,
            "mac_address": "not-a-valid-mac",
        })
        assert resp.status_code == 422

    async def test_register_nonexistent_branch_rejected(self, client, manager_headers):
        resp = await client.post("/api/v1/devices", headers=manager_headers, json={
            "branch_id": 99999,
            "name": "Orphan TV",
            "display_number": 1,
            "mac_address": "AA:BB:CC:00:11:22",
        })
        assert resp.status_code == 404

    async def test_get_device_by_id(self, client, manager_headers, device):
        resp = await client.get(f"/api/v1/devices/{device.id}", headers=manager_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == device.id

    async def test_get_nonexistent_device(self, client, manager_headers):
        resp = await client.get("/api/v1/devices/99999", headers=manager_headers)
        assert resp.status_code == 404

    async def test_update_device_theme(self, client, manager_headers, device):
        resp = await client.patch(
            f"/api/v1/devices/{device.id}",
            headers=manager_headers,
            json={"theme_id": 3}
        )
        assert resp.status_code == 200
        assert resp.json()["theme_id"] == 3

    async def test_update_device_session(self, client, manager_headers, device):
        resp = await client.patch(
            f"/api/v1/devices/{device.id}",
            headers=manager_headers,
            json={"active_session": "lunch"}
        )
        assert resp.status_code == 200
        assert resp.json()["active_session"] == "lunch"

    async def test_delete_device(self, client, manager_headers, branch, db_session):
        from app.models import Device, SessionPeriod
        d = Device(
            branch_id=branch.id, name="Temp TV",
            display_number=9, mac_address="FF:EE:DD:CC:BB:AA"
        )
        db_session.add(d)
        await db_session.commit()

        resp = await client.delete(f"/api/v1/devices/{d.id}", headers=manager_headers)
        assert resp.status_code == 204

    async def test_device_heartbeat_updates_status(self, client, device, db_session):
        resp = await client.post(
            f"/api/v1/devices/{device.id}/heartbeat",
            params={"mac_address": "AA:BB:CC:DD:EE:FF"}
        )
        assert resp.status_code == 200
        await db_session.refresh(device)
        assert device.last_seen is not None
        from app.models import DeviceStatus
        assert device.status == DeviceStatus.ACTIVE

    async def test_device_heartbeat_wrong_mac_rejected(self, client, device):
        resp = await client.post(
            f"/api/v1/devices/{device.id}/heartbeat",
            params={"mac_address": "00:00:00:00:00:00"}
        )
        assert resp.status_code == 404

    async def test_staff_cannot_register_device(self, client, staff_headers, branch):
        resp = await client.post("/api/v1/devices", headers=staff_headers, json={
            "branch_id": branch.id, "name": "TV", "display_number": 7,
            "mac_address": "AA:AA:AA:AA:AA:AA",
        })
        assert resp.status_code == 403
