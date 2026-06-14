"""
LAYER 1 — Unit Tests: Schema Validation
Tests Pydantic v2 schema validation rules, field validators, edge cases.
No DB, no network.
"""
import pytest
from pydantic import ValidationError
from app.schemas import (
    MenuItemCreate, MenuItemUpdate, MenuGroupCreate,
    DeviceCreate, UserCreate, LoginRequest
)


class TestMenuItemCreate:
    def test_valid_item(self):
        item = MenuItemCreate(name="Masala Dosa", price=80.0)
        assert item.name == "Masala Dosa"
        assert item.price == 80.0
        assert item.is_veg is True  # default
        assert item.status.value == "available"  # default
        assert item.session.value == "all_day"  # default

    def test_price_rounds_to_two_decimals(self):
        item = MenuItemCreate(name="Dosa", price=80.999)
        assert item.price == 81.0  # rounded

    def test_price_zero_is_valid(self):
        item = MenuItemCreate(name="Free Item", price=0.0)
        assert item.price == 0.0

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError) as exc:
            MenuItemCreate(name="Bad Item", price=-10.0)
        assert "Price cannot be negative" in str(exc.value)

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(name="", price=50.0)

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(price=50.0)

    def test_all_status_values(self):
        for status in ["available", "not_available", "today_special"]:
            item = MenuItemCreate(name="Item", price=10.0, status=status)
            assert item.status.value == status

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(name="Item", price=10.0, status="sold_out")

    def test_all_session_values(self):
        for session in ["breakfast", "lunch", "dinner", "all_day"]:
            item = MenuItemCreate(name="Item", price=10.0, session=session)
            assert item.session.value == session

    def test_nonveg_item(self):
        item = MenuItemCreate(name="Chicken Curry", price=150.0, is_veg=False)
        assert item.is_veg is False

    def test_optional_fields_default_none(self):
        item = MenuItemCreate(name="Item", price=50.0)
        assert item.name_local is None
        assert item.description is None


class TestMenuItemUpdate:
    def test_all_fields_optional(self):
        """Update schema must allow partial updates."""
        update = MenuItemUpdate()
        assert update.model_dump(exclude_unset=True) == {}

    def test_partial_update(self):
        update = MenuItemUpdate(price=90.0)
        data = update.model_dump(exclude_unset=True)
        assert data == {"price": 90.0}

    def test_negative_price_in_update_raises(self):
        with pytest.raises(ValidationError):
            MenuItemUpdate(price=-5.0)


class TestMenuGroupCreate:
    def test_valid_group(self):
        g = MenuGroupCreate(name="South Indian", sequence=1)
        assert g.name == "South Indian"
        assert g.sequence == 1

    def test_sequence_defaults_to_zero(self):
        g = MenuGroupCreate(name="Beverages")
        assert g.sequence == 0

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            MenuGroupCreate(name="")

    def test_optional_local_name(self):
        g = MenuGroupCreate(name="Beverages", name_local="பானங்கள்")
        assert g.name_local == "பானங்கள்"


class TestDeviceCreate:
    def test_valid_device(self):
        d = DeviceCreate(
            branch_id=1,
            name="Main TV",
            display_number=1,
            mac_address="AA:BB:CC:DD:EE:FF",
        )
        assert d.mac_address == "AA:BB:CC:DD:EE:FF"

    def test_mac_uppercased(self):
        d = DeviceCreate(
            branch_id=1, name="TV", display_number=1,
            mac_address="aa:bb:cc:dd:ee:ff",
        )
        assert d.mac_address == "AA:BB:CC:DD:EE:FF"

    def test_invalid_mac_raises(self):
        with pytest.raises(ValidationError) as exc:
            DeviceCreate(
                branch_id=1, name="TV", display_number=1,
                mac_address="not-a-mac",
            )
        assert "Invalid MAC address" in str(exc.value)

    def test_mac_wrong_length_raises(self):
        with pytest.raises(ValidationError):
            DeviceCreate(
                branch_id=1, name="TV", display_number=1,
                mac_address="AA:BB:CC:DD:EE",  # only 5 groups
            )


class TestUserCreate:
    def test_valid_user(self):
        u = UserCreate(
            username="testuser", email="test@example.com",
            full_name="Test User", password="Password@1234",
        )
        assert u.username == "testuser"

    def test_short_password_raises(self):
        with pytest.raises(ValidationError) as exc:
            UserCreate(
                username="u", email="u@e.com",
                full_name="User", password="short",
            )
        assert "at least 8 characters" in str(exc.value)

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="u", email="not-an-email",
                full_name="User", password="Password@1234",
            )

    def test_default_role_is_staff(self):
        u = UserCreate(
            username="u", email="u@example.com",
            full_name="User", password="Password@1234",
        )
        assert u.role.value == "staff"
