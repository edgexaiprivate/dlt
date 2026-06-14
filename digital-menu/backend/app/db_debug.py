import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import settings

def safe_str(s):
    if s is None:
        return "None"
    return str(s).encode('ascii', errors='replace').decode('ascii')

async def debug_db():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Check groups
        print("\n=== MENU GROUPS ===")
        res = await session.execute(text("SELECT id, restaurant_id, name, is_active FROM menu_groups"))
        groups = res.all()
        for g in groups:
            print(f"Group ID: {g.id}, Restaurant ID: {g.restaurant_id}, Name: {safe_str(g.name)}, Active: {g.is_active}")
            
        # Check subgroups
        print("\n=== MENU SUB GROUPS ===")
        res = await session.execute(text("SELECT id, group_id, name, is_active FROM menu_sub_groups"))
        subgroups = res.all()
        for sg in subgroups:
            print(f"Subgroup ID: {sg.id}, Group ID: {sg.group_id}, Name: {safe_str(sg.name)}, Active: {sg.is_active}")
            
        # Check items
        print("\n=== MENU ITEMS ===")
        res = await session.execute(text("SELECT id, sub_group_id, name, status, price FROM menu_items"))
        items = res.all()
        print(f"Found {len(items)} items in DB:")
        for i in items:
            print(f"Item ID: {i.id}, Subgroup ID: {i.sub_group_id}, Name: {safe_str(i.name)}, Status: {i.status}, Price: {i.price}")

if __name__ == "__main__":
    asyncio.run(debug_db())
