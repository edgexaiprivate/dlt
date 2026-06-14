"""
LAYER 2 — Integration Tests: Role-Based Access Control
Exhaustive matrix tests for all roles × all protected endpoints.

Role matrix:
  super_admin → all access
  manager     → own restaurant only
  staff       → read-only
  anonymous   → public endpoints only
"""
import pytest


class TestRBACMatrix:
    """
    Each test name format: test_{role}_can/cannot_{action}
    Every row in this matrix must pass for deployment to be safe.
    """

    # ── Super Admin ───────────────────────────────────────────────────────────

    async def test_super_admin_can_list_all_restaurants(self, client, admin_headers, restaurant):
        resp = await client.get("/api/v1/restaurants", headers=admin_headers)
        assert resp.status_code == 200

    async def test_super_admin_can_create_restaurant(self, client, admin_headers):
        resp = await client.post("/api/v1/restaurants", headers=admin_headers, json={
            "name": "New Restaurant", "slug": "new-restaurant"
        })
        assert resp.status_code == 201

    async def test_super_admin_can_list_all_users(self, client, admin_headers, manager):
        resp = await client.get("/api/v1/users", headers=admin_headers)
        assert resp.status_code == 200
        # Super admin sees all users
        assert len(resp.json()) >= 1

    async def test_super_admin_can_create_any_role(self, client, admin_headers, restaurant):
        resp = await client.post("/api/v1/users", headers=admin_headers, json={
            "username": "newadmin2", "email": "newadmin2@test.com",
            "full_name": "New Admin", "password": "Admin@12345",
            "role": "super_admin",
        })
        assert resp.status_code == 201

    # ── Manager ───────────────────────────────────────────────────────────────

    async def test_manager_can_create_menu_group(self, client, manager_headers, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=manager_headers,
            json={"name": "RBAC Test Group", "sequence": 99}
        )
        assert resp.status_code == 201

    async def test_manager_cannot_create_restaurant(self, client, manager_headers):
        resp = await client.post("/api/v1/restaurants", headers=manager_headers, json={
            "name": "Sneaky Restaurant", "slug": "sneaky"
        })
        assert resp.status_code == 403

    async def test_manager_cannot_create_super_admin_user(self, client, manager_headers):
        resp = await client.post("/api/v1/users", headers=manager_headers, json={
            "username": "sneakyadmin", "email": "sneaky@test.com",
            "full_name": "Sneaky", "password": "Admin@12345",
            "role": "super_admin",
        })
        assert resp.status_code == 403

    async def test_manager_can_create_staff_user(self, client, manager_headers, restaurant):
        resp = await client.post("/api/v1/users", headers=manager_headers, json={
            "username": "newstaff99", "email": "newstaff99@test.com",
            "full_name": "New Staff", "password": "Staff@12345",
            "role": "staff", "restaurant_id": restaurant.id,
        })
        assert resp.status_code == 201

    async def test_manager_can_publish_own_restaurant_menu(self, client, manager_headers, restaurant):
        from unittest.mock import AsyncMock, patch
        with patch("app.api.v1.endpoints.menu.publish_menu_update", new_callable=AsyncMock):
            with patch("app.api.v1.endpoints.menu.cache_delete_pattern", new_callable=AsyncMock):
                resp = await client.post(
                    f"/api/v1/menu/restaurants/{restaurant.id}/publish",
                    headers=manager_headers
                )
        assert resp.status_code == 200

    async def test_manager_cannot_access_other_restaurant_menu(
        self, client, manager_headers, db_session
    ):
        from app.models import Restaurant
        other = Restaurant(name="Other Restaurant", slug="other-restaurant")
        db_session.add(other)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/menu/restaurants/{other.id}/groups",
            headers=manager_headers
        )
        assert resp.status_code == 403

    # ── Staff ─────────────────────────────────────────────────────────────────

    async def test_staff_can_read_menu_groups(self, client, staff_headers, restaurant, menu_group):
        resp = await client.get(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=staff_headers
        )
        assert resp.status_code == 200

    async def test_staff_cannot_create_menu_group(self, client, staff_headers, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=staff_headers,
            json={"name": "Staff Attempt", "sequence": 1}
        )
        assert resp.status_code == 403

    async def test_staff_cannot_delete_menu_item(self, client, staff_headers, menu_item):
        resp = await client.delete(f"/api/v1/menu/items/{menu_item.id}", headers=staff_headers)
        assert resp.status_code == 403

    async def test_staff_cannot_register_device(self, client, staff_headers, branch):
        resp = await client.post("/api/v1/devices", headers=staff_headers, json={
            "branch_id": branch.id, "name": "TV", "display_number": 8,
            "mac_address": "BB:BB:BB:BB:BB:BB",
        })
        assert resp.status_code == 403

    async def test_staff_can_view_devices(self, client, staff_headers, device):
        resp = await client.get("/api/v1/devices", headers=staff_headers)
        assert resp.status_code == 200

    async def test_staff_cannot_publish(self, client, staff_headers, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/publish",
            headers=staff_headers
        )
        assert resp.status_code == 403

    # ── Anonymous ─────────────────────────────────────────────────────────────

    async def test_anonymous_can_access_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_anonymous_cannot_access_menu(self, client, restaurant):
        resp = await client.get(f"/api/v1/menu/restaurants/{restaurant.id}/groups")
        assert resp.status_code == 403

    async def test_anonymous_cannot_list_users(self, client):
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_anonymous_cannot_list_devices(self, client):
        resp = await client.get("/api/v1/devices")
        assert resp.status_code == 403

    async def test_wrong_token_format_rejected(self, client, restaurant):
        resp = await client.get(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers={"Authorization": "Token abc123"}  # wrong scheme
        )
        assert resp.status_code == 403
