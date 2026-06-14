"""
Seed script — run once after `alembic upgrade head`.
Creates a default super admin and a sample restaurant with menu.

Usage:
    cd backend
    python -m scripts.seed
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal, engine
from app.database_models import Base, User, UserRole, Restaurant, Branch, MenuGroup, MenuSubGroup, MenuItem, ItemStatus, SessionPeriod
from app.core.security import hash_password


async def seed():
    # Create tables (in dev — in prod use alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ── Super Admin ────────────────────────────────────────────────────
        existing_admin = await db.execute(
            __import__("sqlalchemy").select(User).where(User.username == "admin")
        )
        if not existing_admin.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@menuvision.app",
                full_name="Super Admin",
                hashed_password=hash_password("Admin@1234"),
                role=UserRole.SUPER_ADMIN,
            )
            db.add(admin)
            print("✅ Created super admin: admin / Admin@1234")

        # ── Sample Restaurant ──────────────────────────────────────────────
        from sqlalchemy import select
        existing_rest = await db.execute(select(Restaurant).where(Restaurant.slug == "hotel-saravana"))
        restaurant = existing_rest.scalar_one_or_none()

        if not restaurant:
            restaurant = Restaurant(name="Hotel Saravana Bhavan", slug="hotel-saravana")
            db.add(restaurant)
            await db.flush()

            branch = Branch(restaurant_id=restaurant.id, name="Main Branch", location="MG Road, Bangalore")
            db.add(branch)

            # Menu Manager user
            manager = User(
                username="manager1",
                email="manager@saravana.com",
                full_name="Ravi Kumar",
                hashed_password=hash_password("Manager@1234"),
                role=UserRole.MANAGER,
                restaurant_id=restaurant.id,
            )
            db.add(manager)

            # ── Menu groups ───────────────────────────────────────────────
            groups_data = [
                {
                    "name": "South Indian", "name_local": "தென்னிந்திய உணவு",
                    "instruction": "Pure Veg | GST Included", "sequence": 1,
                    "sub_groups": [
                        {
                            "name": "Dosa", "sequence": 1,
                            "items": [
                                {"name": "Plain Dosa", "price": 60, "sequence": 1},
                                {"name": "Masala Dosa", "price": 80, "sequence": 2},
                                {"name": "Ghee Roast Dosa", "price": 100, "sequence": 3},
                                {"name": "Paper Dosa", "price": 70, "sequence": 4},
                                {"name": "Set Dosa", "price": 70, "sequence": 5},
                            ]
                        },
                        {
                            "name": "Idli", "sequence": 2,
                            "items": [
                                {"name": "Plain Idli (2 pcs)", "price": 50, "sequence": 1},
                                {"name": "Ghee Idli", "price": 65, "sequence": 2},
                                {"name": "Sambar Idli", "price": 70, "sequence": 3},
                            ]
                        },
                        {
                            "name": "Pongal & Upma", "sequence": 3,
                            "items": [
                                {"name": "Ven Pongal", "price": 70, "sequence": 1},
                                {"name": "Khara Bath", "price": 65, "sequence": 2},
                                {"name": "Kesari Bath", "price": 55, "sequence": 3},
                            ]
                        }
                    ]
                },
                {
                    "name": "Beverages", "name_local": "பானங்கள்",
                    "instruction": "Fresh & Hot", "sequence": 2,
                    "sub_groups": [
                        {
                            "name": "Tea & Coffee", "sequence": 1,
                            "items": [
                                {"name": "Filter Coffee", "price": 35, "sequence": 1},
                                {"name": "Tea", "price": 25, "sequence": 2},
                                {"name": "Bru Coffee", "price": 30, "sequence": 3},
                            ]
                        },
                        {
                            "name": "Cold Drinks", "sequence": 2,
                            "items": [
                                {"name": "Fresh Lime Soda", "price": 60, "sequence": 1},
                                {"name": "Buttermilk", "price": 30, "sequence": 2},
                                {"name": "Lassi", "price": 70, "sequence": 3},
                            ]
                        }
                    ]
                },
                {
                    "name": "North Indian", "name_local": "उत्तर भारतीय",
                    "instruction": "Chef's Special", "sequence": 3,
                    "sub_groups": [
                        {
                            "name": "Breads", "sequence": 1,
                            "items": [
                                {"name": "Chapati", "price": 15, "sequence": 1},
                                {"name": "Paratha", "price": 60, "sequence": 2},
                                {"name": "Puri Bhaji", "price": 80, "sequence": 3},
                            ]
                        }
                    ]
                }
            ]

            for gd in groups_data:
                sub_groups_data = gd.pop("sub_groups")
                group = MenuGroup(restaurant_id=restaurant.id, **gd)
                db.add(group)
                await db.flush()

                for sgd in sub_groups_data:
                    items_data = sgd.pop("items")
                    subgroup = MenuSubGroup(group_id=group.id, **sgd)
                    db.add(subgroup)
                    await db.flush()

                    for itd in items_data:
                        item = MenuItem(
                            sub_group_id=subgroup.id,
                            is_veg=True,
                            status=ItemStatus.AVAILABLE,
                            session=SessionPeriod.ALL_DAY,
                            **itd
                        )
                        db.add(item)

            print("✅ Created sample restaurant: Hotel Saravana Bhavan")
            print("   Manager login: manager1 / Manager@1234")

        await db.commit()
        print("\n🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
