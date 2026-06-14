"""
LAYER 1 — Unit Tests: Models
Tests model defaults, enum values, relationship configuration.
Uses in-memory SQLite via conftest fixtures.
"""
import pytest
from datetime import datetime
from app.models import (
    User, Restaurant, Branch, MenuGroup, MenuSubGroup, MenuItem, Device,
    UserRole, ItemStatus, SessionPeriod, DeviceStatus
)
from app.core.security import hash_password


class TestUserModel:
    async def test_user_defaults(self, db_session):
        u = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=hash_password("Pass@1234"),
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)

        assert u.id is not None
        assert u.is_active is True
        assert u.role == UserRole.STAFF
        assert isinstance(u.created_at, datetime)
        assert u.last_login is None
        assert u.restaurant_id is None

    async def test_user_role_enum_values(self):
        assert UserRole.SUPER_ADMIN.value == "super_admin"
        assert UserRole.MANAGER.value == "manager"
        assert UserRole.STAFF.value == "staff"

    async def test_super_admin_role(self, db_session):
        u = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin",
            hashed_password=hash_password("Admin@1234"),
            role=UserRole.SUPER_ADMIN,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        assert u.role == UserRole.SUPER_ADMIN

    async def test_inactive_user(self, db_session):
        u = User(
            username="inactive",
            email="inactive@example.com",
            full_name="Inactive",
            hashed_password=hash_password("Pass@1234"),
            is_active=False,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        assert u.is_active is False


class TestRestaurantModel:
    async def test_restaurant_defaults(self, db_session):
        r = Restaurant(name="Hotel Test", slug="hotel-test")
        db_session.add(r)
        await db_session.commit()
        await db_session.refresh(r)

        assert r.id is not None
        assert r.is_active is True
        assert r.logo_url is None
        assert isinstance(r.created_at, datetime)

    async def test_slug_uniqueness(self, db_session):
        r1 = Restaurant(name="Hotel A", slug="same-slug")
        r2 = Restaurant(name="Hotel B", slug="same-slug")
        db_session.add(r1)
        await db_session.commit()
        db_session.add(r2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()


class TestMenuItemModel:
    async def test_item_defaults(self, db_session, menu_sub_group):
        item = MenuItem(
            sub_group_id=menu_sub_group.id,
            name="Plain Dosa",
            price=60.0,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.id is not None
        assert item.is_veg is True
        assert item.status == ItemStatus.AVAILABLE
        assert item.session == SessionPeriod.ALL_DAY
        assert item.sequence == 0
        assert item.image_url is None
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)

    async def test_item_status_enum(self):
        assert ItemStatus.AVAILABLE.value == "available"
        assert ItemStatus.NOT_AVAILABLE.value == "not_available"
        assert ItemStatus.TODAY_SPECIAL.value == "today_special"

    async def test_session_period_enum(self):
        assert SessionPeriod.BREAKFAST.value == "breakfast"
        assert SessionPeriod.LUNCH.value == "lunch"
        assert SessionPeriod.DINNER.value == "dinner"
        assert SessionPeriod.ALL_DAY.value == "all_day"

    async def test_nonveg_item(self, db_session, menu_sub_group):
        item = MenuItem(
            sub_group_id=menu_sub_group.id,
            name="Chicken Curry",
            price=150.0,
            is_veg=False,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        assert item.is_veg is False


class TestDeviceModel:
    async def test_device_defaults(self, db_session, branch):
        d = Device(
            branch_id=branch.id,
            name="TV 1",
            display_number=1,
            mac_address="11:22:33:44:55:66",
        )
        db_session.add(d)
        await db_session.commit()
        await db_session.refresh(d)

        assert d.id is not None
        assert d.status == DeviceStatus.UNREGISTERED
        assert d.theme_id == 1
        assert d.active_session == SessionPeriod.ALL_DAY
        assert d.last_seen is None

    async def test_mac_uniqueness(self, db_session, branch):
        d1 = Device(branch_id=branch.id, name="TV 1", display_number=1, mac_address="AA:BB:CC:DD:EE:01")
        d2 = Device(branch_id=branch.id, name="TV 2", display_number=2, mac_address="AA:BB:CC:DD:EE:01")
        db_session.add(d1)
        await db_session.commit()
        db_session.add(d2)
        with pytest.raises(Exception):  # IntegrityError — duplicate MAC
            await db_session.commit()
