"""
LAYER 2 — Integration Tests: Menu API
Tests full CRUD for MenuGroup → MenuSubGroup → MenuItem hierarchy,
role-based access control, and the publish endpoint.

Mandatory cases:
  - Manager can create/read/update/delete own restaurant's menu
  - Manager cannot touch another restaurant's menu
  - Staff can only read (no write)
  - Item price validation enforced at API level
  - Publish endpoint triggers Redis event (mocked)
  - Full menu tree returns correct nesting
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestMenuGroups:
    async def test_list_groups_authenticated(self, client, manager_headers, restaurant, menu_group):
        resp = await client.get(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=manager_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "South Indian"

    async def test_list_groups_requires_auth(self, client, restaurant):
        resp = await client.get(f"/api/v1/menu/restaurants/{restaurant.id}/groups")
        assert resp.status_code == 403

    async def test_create_group_as_manager(self, client, manager_headers, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=manager_headers,
            json={"name": "Beverages", "instruction": "Fresh & Hot", "sequence": 2}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Beverages"
        assert data["instruction"] == "Fresh & Hot"
        assert data["sequence"] == 2
        assert data["is_active"] is True
        assert data["restaurant_id"] == restaurant.id

    async def test_create_group_staff_forbidden(self, client, staff_headers, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=staff_headers,
            json={"name": "New Cat", "sequence": 1}
        )
        assert resp.status_code == 403

    async def test_create_group_unauthenticated_forbidden(self, client, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            json={"name": "New Cat", "sequence": 1}
        )
        assert resp.status_code == 403

    async def test_update_group(self, client, manager_headers, menu_group):
        resp = await client.patch(
            f"/api/v1/menu/groups/{menu_group.id}",
            headers=manager_headers,
            json={"name": "Updated Name", "instruction": "New instruction"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_update_group_partial(self, client, manager_headers, menu_group):
        """PATCH must support partial updates — only specified fields change."""
        original_instruction = menu_group.instruction
        resp = await client.patch(
            f"/api/v1/menu/groups/{menu_group.id}",
            headers=manager_headers,
            json={"name": "Only Name Changed"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Only Name Changed"
        assert resp.json()["instruction"] == original_instruction

    async def test_toggle_group_active(self, client, manager_headers, menu_group):
        resp = await client.patch(
            f"/api/v1/menu/groups/{menu_group.id}",
            headers=manager_headers,
            json={"is_active": False}
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_delete_group(self, client, manager_headers, restaurant, db_session):
        from app.models import MenuGroup
        g = MenuGroup(restaurant_id=restaurant.id, name="To Delete", sequence=99)
        db_session.add(g)
        await db_session.commit()

        resp = await client.delete(f"/api/v1/menu/groups/{g.id}", headers=manager_headers)
        assert resp.status_code == 204

        # Verify deleted
        check = await client.get(
            f"/api/v1/menu/restaurants/{restaurant.id}/groups",
            headers=manager_headers
        )
        names = [g["name"] for g in check.json()]
        assert "To Delete" not in names

    async def test_delete_nonexistent_group(self, client, manager_headers):
        resp = await client.delete("/api/v1/menu/groups/99999", headers=manager_headers)
        assert resp.status_code == 404


class TestMenuSubGroups:
    async def test_create_subgroup(self, client, manager_headers, menu_group):
        resp = await client.post(
            f"/api/v1/menu/groups/{menu_group.id}/subgroups",
            headers=manager_headers,
            json={"name": "Idli", "sequence": 2}
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Idli"
        assert resp.json()["group_id"] == menu_group.id

    async def test_list_subgroups(self, client, manager_headers, menu_group, menu_sub_group):
        resp = await client.get(
            f"/api/v1/menu/groups/{menu_group.id}/subgroups",
            headers=manager_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Dosa"

    async def test_update_subgroup(self, client, manager_headers, menu_sub_group):
        resp = await client.patch(
            f"/api/v1/menu/subgroups/{menu_sub_group.id}",
            headers=manager_headers,
            json={"name": "Special Dosa", "sequence": 5}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Special Dosa"

    async def test_delete_subgroup(self, client, manager_headers, menu_group, db_session):
        from app.models import MenuSubGroup
        sg = MenuSubGroup(group_id=menu_group.id, name="Temp", sequence=99)
        db_session.add(sg)
        await db_session.commit()

        resp = await client.delete(f"/api/v1/menu/subgroups/{sg.id}", headers=manager_headers)
        assert resp.status_code == 204


class TestMenuItems:
    async def test_create_item(self, client, manager_headers, menu_sub_group):
        resp = await client.post(
            f"/api/v1/menu/subgroups/{menu_sub_group.id}/items",
            headers=manager_headers,
            json={
                "name": "Ghee Dosa",
                "price": 100.0,
                "is_veg": True,
                "status": "available",
                "session": "all_day",
                "sequence": 1,
            }
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Ghee Dosa"
        assert data["price"] == 100.0
        assert data["is_veg"] is True

    async def test_create_item_negative_price_rejected(self, client, manager_headers, menu_sub_group):
        resp = await client.post(
            f"/api/v1/menu/subgroups/{menu_sub_group.id}/items",
            headers=manager_headers,
            json={"name": "Bad Item", "price": -50.0}
        )
        assert resp.status_code == 422

    async def test_list_items_ordered_by_sequence(self, client, manager_headers, menu_sub_group, db_session):
        from app.models import MenuItem, ItemStatus, SessionPeriod
        items = [
            MenuItem(sub_group_id=menu_sub_group.id, name="C", price=30.0, sequence=3),
            MenuItem(sub_group_id=menu_sub_group.id, name="A", price=10.0, sequence=1),
            MenuItem(sub_group_id=menu_sub_group.id, name="B", price=20.0, sequence=2),
        ]
        for i in items:
            db_session.add(i)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/menu/subgroups/{menu_sub_group.id}/items",
            headers=manager_headers
        )
        assert resp.status_code == 200
        names = [i["name"] for i in resp.json()]
        assert names == ["A", "B", "C"]

    async def test_update_item_status(self, client, manager_headers, menu_item):
        resp = await client.patch(
            f"/api/v1/menu/items/{menu_item.id}",
            headers=manager_headers,
            json={"status": "not_available"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_available"

    async def test_update_item_mark_special(self, client, manager_headers, menu_item):
        resp = await client.patch(
            f"/api/v1/menu/items/{menu_item.id}",
            headers=manager_headers,
            json={"status": "today_special"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "today_special"

    async def test_update_nonexistent_item(self, client, manager_headers):
        resp = await client.patch(
            "/api/v1/menu/items/99999",
            headers=manager_headers,
            json={"price": 50.0}
        )
        assert resp.status_code == 404

    async def test_delete_item(self, client, manager_headers, menu_item):
        resp = await client.delete(f"/api/v1/menu/items/{menu_item.id}", headers=manager_headers)
        assert resp.status_code == 204

    async def test_staff_cannot_create_item(self, client, staff_headers, menu_sub_group):
        resp = await client.post(
            f"/api/v1/menu/subgroups/{menu_sub_group.id}/items",
            headers=staff_headers,
            json={"name": "Forbidden Item", "price": 50.0}
        )
        assert resp.status_code == 403


class TestFullMenuAndPublish:
    async def test_full_menu_returns_nested_tree(self, client, manager_headers, restaurant, menu_item):
        resp = await client.get(
            f"/api/v1/menu/restaurants/{restaurant.id}/full",
            headers=manager_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "restaurant" in data
        assert "groups" in data
        assert data["restaurant"]["id"] == restaurant.id
        # Check nesting: groups → sub_groups → items
        groups = data["groups"]
        assert len(groups) >= 1
        assert "sub_groups" in groups[0]
        assert "items" in groups[0]["sub_groups"][0]
        assert groups[0]["sub_groups"][0]["items"][0]["name"] == "Masala Dosa"

    async def test_publish_triggers_redis_event(self, client, manager_headers, restaurant):
        with patch("app.api.v1.endpoints.menu.publish_menu_update", new_callable=AsyncMock) as mock_pub:
            with patch("app.api.v1.endpoints.menu.cache_delete_pattern", new_callable=AsyncMock):
                resp = await client.post(
                    f"/api/v1/menu/restaurants/{restaurant.id}/publish",
                    headers=manager_headers
                )
        assert resp.status_code == 200
        mock_pub.assert_called_once()
        call_args = mock_pub.call_args
        assert call_args[0][0] == restaurant.id
        assert call_args[0][1]["event"] == "menu_published"

    async def test_publish_staff_forbidden(self, client, staff_headers, restaurant):
        resp = await client.post(
            f"/api/v1/menu/restaurants/{restaurant.id}/publish",
            headers=staff_headers
        )
        assert resp.status_code == 403

    async def test_publish_unauthenticated_forbidden(self, client, restaurant):
        resp = await client.post(f"/api/v1/menu/restaurants/{restaurant.id}/publish")
        assert resp.status_code == 403
