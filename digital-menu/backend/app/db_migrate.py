import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import settings
async def run_migration():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        print("Checking if expires_at column exists in menu_items table...")
        # Check column existence in PostgreSQL
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='menu_items' AND column_name='expires_at';
        """
        res = await session.execute(text(check_query))
        exists = res.scalar_one_or_none()
        
        if not exists:
            print("expires_at column does not exist. Adding it...")
            alter_query = "ALTER TABLE menu_items ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;"
            await session.execute(text(alter_query))
            await session.commit()
            print("Successfully added expires_at column to menu_items table!")
        else:
            print("expires_at column already exists.")
if __name__ == "__main__":
    asyncio.run(run_migration())



# TestClient.py 
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.database_models import User, UserRole
mock_user = User(
    id=1,
    username="admin",
    email="admin@example.com",
    role=UserRole.SUPER_ADMIN,
    restaurant_id=1,
    is_active=True
)
async def override_get_current_user():
    return mock_user
app.dependency_overrides[get_current_user] = override_get_current_user
def test_api():
    client = TestClient(app)
    
    print("=== GET /api/v1/menu/subgroups/1/items ===")
    res = client.get("/api/v1/menu/subgroups/1/items", headers={"Authorization": "Bearer mock"})
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
    print("\n=== GET /api/v1/menu/restaurants/1/full ===")
    res = client.get("/api/v1/menu/restaurants/1/full", headers={"Authorization": "Bearer mock"})
    print(f"Status: {res.status_code}")
    print(f"Response length: {len(res.text)}")
    print(f"Response: {res.text[:1000]}")
if __name__ == "__main__":
    test_api()
if __name__ == "__main__":
    test_api()
