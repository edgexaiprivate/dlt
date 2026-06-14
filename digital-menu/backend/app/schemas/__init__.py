"""
Pydantic v2 schemas — request/response validation for all API endpoints.
"""
from pydantic import BaseModel, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.database_models import UserRole, ItemStatus, DeviceStatus, SessionPeriod


# ─── Base ─────────────────────────────────────────────────────────────────────

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.STAFF
    restaurant_id: Optional[int] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    restaurant_id: Optional[int] = None


class UserPasswordReset(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    restaurant_id: Optional[int]
    created_at: datetime
    last_login: Optional[datetime]


# ─── Restaurant ───────────────────────────────────────────────────────────────

class RestaurantCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    logo_url: Optional[str]
    is_active: bool
    created_at: datetime


# ─── Branch ───────────────────────────────────────────────────────────────────

class BranchCreate(BaseModel):
    name: str
    location: Optional[str] = None


class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    location: Optional[str]
    is_active: bool
    created_at: datetime


# ─── Device ───────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    branch_id: int
    name: str
    display_number: int
    mac_address: Optional[str] = None
    screen_size_inch: Optional[int] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    theme_id: int = 1
    active_session: SessionPeriod = SessionPeriod.ALL_DAY

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v is None or not v.strip():
            return None
        if not re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", v):
            raise ValueError("Invalid MAC address format (expected XX:XX:XX:XX:XX:XX)")
        return v.upper()


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    display_number: Optional[int] = None
    screen_size_inch: Optional[int] = None
    theme_id: Optional[int] = None
    active_session: Optional[SessionPeriod] = None
    status: Optional[DeviceStatus] = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    name: str
    display_number: int
    mac_address: str
    screen_size_inch: Optional[int]
    resolution_width: Optional[int]
    resolution_height: Optional[int]
    status: DeviceStatus
    theme_id: int
    active_session: SessionPeriod
    last_seen: Optional[datetime]
    registered_at: datetime


# ─── Menu Group ───────────────────────────────────────────────────────────────

class MenuGroupCreate(BaseModel):
    name: str
    name_local: Optional[str] = None
    instruction: Optional[str] = None
    sequence: int = 0


class MenuGroupUpdate(BaseModel):
    name: Optional[str] = None
    name_local: Optional[str] = None
    instruction: Optional[str] = None
    sequence: Optional[int] = None
    is_active: Optional[bool] = None


class MenuGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    name_local: Optional[str]
    instruction: Optional[str]
    sequence: int
    is_active: bool
    image_url: Optional[str]
    created_at: datetime


class MenuGroupWithChildren(MenuGroupOut):
    sub_groups: List["MenuSubGroupWithItems"] = []


# ─── Menu Sub Group ───────────────────────────────────────────────────────────

class MenuSubGroupCreate(BaseModel):
    name: str
    name_local: Optional[str] = None
    sequence: int = 0


class MenuSubGroupUpdate(BaseModel):
    name: Optional[str] = None
    name_local: Optional[str] = None
    sequence: Optional[int] = None
    is_active: Optional[bool] = None


class MenuSubGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    name: str
    name_local: Optional[str]
    sequence: int
    is_active: bool
    created_at: datetime


class MenuSubGroupWithItems(MenuSubGroupOut):
    items: List["MenuItemOut"] = []


# ─── Menu Item ────────────────────────────────────────────────────────────────

class MenuItemCreate(BaseModel):
    name: str
    name_local: Optional[str] = None
    description: Optional[str] = None
    price: float
    is_veg: bool = True
    sequence: int = 0
    session: SessionPeriod = SessionPeriod.ALL_DAY
    status: ItemStatus = ItemStatus.AVAILABLE

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2)


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    name_local: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_veg: Optional[bool] = None
    sequence: Optional[int] = None
    session: Optional[SessionPeriod] = None
    status: Optional[ItemStatus] = None
    image_url: Optional[str] = None

    @field_validator("price", mode="before")
    @classmethod
    def price_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2) if v is not None else v


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sub_group_id: int
    name: str
    name_local: Optional[str]
    description: Optional[str]
    price: float
    image_url: Optional[str]
    status: ItemStatus
    is_veg: bool
    sequence: int
    session: SessionPeriod
    created_at: datetime
    updated_at: datetime

class ReorderItemsRequest(BaseModel):
    ids: List[int]


# ─── Templates ────────────────────────────────────────────────────────────────

class TemplateItemIn(BaseModel):
    item_id: int
    duration_seconds: int = 10


class TemplateCreate(BaseModel):
    name: str
    name_local: Optional[str] = None


class TemplateItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    items_id: int
    duration_second: int
    menu_item: "MenuItemOut"


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    name_local: Optional[str]
    is_active: bool
    items: List["TemplateItemOut"] = []


class TemplateSaveRequest(BaseModel):
    name: str
    name_local: Optional[str] = None
    items: List[TemplateItemIn]

# ─── Full Menu Response (for TV display) ─────────────────────────────────────

class FullMenuResponse(BaseModel):
    restaurant: RestaurantOut
    groups: List[MenuGroupWithChildren]
    published_at: datetime


# Update forward references
MenuGroupWithChildren.model_rebuild()
MenuSubGroupWithItems.model_rebuild()
TemplateItemOut.model_rebuild()
TemplateOut.model_rebuild()


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int
