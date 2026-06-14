"""
conftest.py — shared fixtures for all test layers.

Uses SQLite (aiosqlite) so tests run without a real Postgres instance.
The DB is created fresh for every test session and tables are wiped per test.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models import User, Restaurant, Branch, MenuGroup, MenuSubGroup, MenuItem, Device
from app.models import UserRole, ItemStatus, SessionPeriod, DeviceStatus
from app.core.security import hash_password, create_access_token

# ── In-memory SQLite engine (no Postgres needed) ──────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession,
    expire_on_commit=False, autocommit=False, autoflush=False,
)


# ── Session-scoped: create tables once per test run ──────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Function-scoped DB session: each test gets a clean state ─────────────────
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
        # Truncate all tables after each test
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


# ── Override FastAPI's get_db to use the test session ─────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Reusable data factories ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def restaurant(db_session: AsyncSession) -> Restaurant:
    r = Restaurant(name="Test Restaurant", slug="test-restaurant")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    return r


@pytest_asyncio.fixture
async def branch(db_session: AsyncSession, restaurant: Restaurant) -> Branch:
    b = Branch(restaurant_id=restaurant.id, name="Main Branch", location="Test City")
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)
    return b


@pytest_asyncio.fixture
async def super_admin(db_session: AsyncSession) -> User:
    u = User(
        username="admin",
        email="admin@test.com",
        full_name="Super Admin",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def manager(db_session: AsyncSession, restaurant: Restaurant) -> User:
    u = User(
        username="manager1",
        email="manager@test.com",
        full_name="Test Manager",
        hashed_password=hash_password("Manager@1234"),
        role=UserRole.MANAGER,
        restaurant_id=restaurant.id,
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def staff_user(db_session: AsyncSession, restaurant: Restaurant) -> User:
    u = User(
        username="staff1",
        email="staff@test.com",
        full_name="Test Staff",
        hashed_password=hash_password("Staff@1234"),
        role=UserRole.STAFF,
        restaurant_id=restaurant.id,
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def menu_group(db_session: AsyncSession, restaurant: Restaurant) -> MenuGroup:
    g = MenuGroup(
        restaurant_id=restaurant.id,
        name="South Indian",
        name_local="தென்னிந்திய உணவு",
        instruction="Pure Veg",
        sequence=1,
        is_active=True,
    )
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)
    return g


@pytest_asyncio.fixture
async def menu_sub_group(db_session: AsyncSession, menu_group: MenuGroup) -> MenuSubGroup:
    sg = MenuSubGroup(
        group_id=menu_group.id,
        name="Dosa",
        sequence=1,
        is_active=True,
    )
    db_session.add(sg)
    await db_session.commit()
    await db_session.refresh(sg)
    return sg


@pytest_asyncio.fixture
async def menu_item(db_session: AsyncSession, menu_sub_group: MenuSubGroup) -> MenuItem:
    item = MenuItem(
        sub_group_id=menu_sub_group.id,
        name="Masala Dosa",
        price=80.0,
        is_veg=True,
        status=ItemStatus.AVAILABLE,
        session=SessionPeriod.ALL_DAY,
        sequence=1,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest_asyncio.fixture
async def device(db_session: AsyncSession, branch: Branch) -> Device:
    d = Device(
        branch_id=branch.id,
        name="Main Hall TV",
        display_number=1,
        mac_address="AA:BB:CC:DD:EE:FF",
        status=DeviceStatus.ACTIVE,
        theme_id=1,
        active_session=SessionPeriod.ALL_DAY,
    )
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


# ── Auth header helpers ───────────────────────────────────────────────────────

def auth_headers(user: User) -> dict:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def admin_headers(super_admin: User) -> dict:
    return auth_headers(super_admin)


@pytest_asyncio.fixture
def manager_headers(manager: User) -> dict:
    return auth_headers(manager)


@pytest_asyncio.fixture
def staff_headers(staff_user: User) -> dict:
    return auth_headers(staff_user)
