from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, ItemStatus, DeviceStatus, SessionPeriod


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
    last_login: Optional[datetime] = None

class RestaurantCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None

class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    logo_url: Optional[str]
    is_active: bool
    created_at: datetime

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

class DeviceCreate(BaseModel):
    branch_id: int
    name: str
    display_number: int
    mac_address: str
    screen_size_inch: Optional[int] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    theme_id: int = 1
    active_session: SessionPeriod = SessionPeriod.ALL_DAY

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v: str) -> str:
        import re
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
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    status: DeviceStatus
    theme_id: int
    active_session: SessionPeriod
    last_seen: Optional[datetime]
    registered_at: datetime

class MenuGroupCreate(BaseModel):
    name: str = Field(..., min_length=1)
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

class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
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

class MenuSubGroupWithItems(MenuSubGroupOut):
    items: List[MenuItemOut] = []

class MenuGroupWithChildren(MenuGroupOut):
    sub_groups: List[MenuSubGroupWithItems] = []

class FullMenuResponse(BaseModel):
    restaurant: RestaurantOut
    groups: List[MenuGroupWithChildren]
    published_at: datetime

MenuGroupWithChildren.model_rebuild()
MenuSubGroupWithItems.model_rebuild()
TokenResponse.model_rebuild()
