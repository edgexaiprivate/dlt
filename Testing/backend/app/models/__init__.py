from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey,
    Text, Float, Enum as SAEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    STAFF = "staff"


class ItemStatus(str, enum.Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    TODAY_SPECIAL = "today_special"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNREGISTERED = "unregistered"


class SessionPeriod(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    ALL_DAY = "all_day"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.STAFF)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    restaurant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("restaurants.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    restaurant: Mapped[Optional["Restaurant"]] = relationship("Restaurant", back_populates="users")


class Restaurant(Base):
    __tablename__ = "restaurants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    branches: Mapped[List["Branch"]] = relationship("Branch", back_populates="restaurant", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship("User", back_populates="restaurant")
    menu_groups: Mapped[List["MenuGroup"]] = relationship("MenuGroup", back_populates="restaurant", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="branches")
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="branch", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_number: Mapped[int] = mapped_column(Integer, nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), unique=True, nullable=False, index=True)
    screen_size_inch: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(SAEnum(DeviceStatus), default=DeviceStatus.UNREGISTERED)
    theme_id: Mapped[int] = mapped_column(Integer, default=1)
    active_session: Mapped[SessionPeriod] = mapped_column(SAEnum(SessionPeriod), default=SessionPeriod.ALL_DAY)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    branch: Mapped["Branch"] = relationship("Branch", back_populates="devices")
    __table_args__ = (UniqueConstraint("branch_id", "display_number", name="uq_branch_display"),)


class MenuGroup(Base):
    __tablename__ = "menu_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_local: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    instruction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_groups")
    sub_groups: Mapped[List["MenuSubGroup"]] = relationship("MenuSubGroup", back_populates="group", cascade="all, delete-orphan")


class MenuSubGroup(Base):
    __tablename__ = "menu_sub_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("menu_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_local: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    group: Mapped["MenuGroup"] = relationship("MenuGroup", back_populates="sub_groups")
    items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="sub_group", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sub_group_id: Mapped[int] = mapped_column(ForeignKey("menu_sub_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    name_local: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[ItemStatus] = mapped_column(SAEnum(ItemStatus), default=ItemStatus.AVAILABLE)
    is_veg: Mapped[bool] = mapped_column(Boolean, default=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    session: Mapped[SessionPeriod] = mapped_column(SAEnum(SessionPeriod), default=SessionPeriod.ALL_DAY)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    sub_group: Mapped["MenuSubGroup"] = relationship("MenuSubGroup", back_populates="items")
