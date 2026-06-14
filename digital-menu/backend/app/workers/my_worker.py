import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database_models import MenuItem, ItemStatus, MenuSubGroup, MenuGroup
from app.db.redis import publish_menu_update, cache_delete_pattern

async def expiration_worker(db_session_factory):
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        try:
            async with db_session_factory() as db:
                now = datetime.now(timezone.utc)
                
                # 1. Find all active items whose expiration time has passed
                result = await db.execute(
                    select(MenuItem)
                    .join(MenuSubGroup, MenuItem.sub_group_id == MenuSubGroup.id)
                    .join(MenuGroup, MenuSubGroup.group_id == MenuGroup.id)
                    .where(
                        MenuItem.status == ItemStatus.AVAILABLE,
                        MenuItem.expires_at <= now
                    )
                    .options(
                        selectinload(MenuItem.sub_group)
                        .selectinload(MenuSubGroup.group)
                    )
                )
                expired_items = result.scalars().all()
                
                if expired_items:
                    restaurant_ids = set()
                    
                    # 2. Update their status to 'not_available' and collect restaurant IDs
                    for item in expired_items:
                        item.status = ItemStatus.NOT_AVAILABLE
                        item.expires_at = None
                        if item.sub_group and item.sub_group.group:
                            restaurant_ids.add(item.sub_group.group.restaurant_id)
                    
                    await db.commit()
                    
                    # 3. Broadcast the menu update to all TVs via WebSockets and delete menu cache
                    for restaurant_id in restaurant_ids:
                        await publish_menu_update(restaurant_id, {"event": "menu_updated"})
                        await cache_delete_pattern(f"menu:{restaurant_id}:*")
        except Exception as e:
            # Prevent the background worker from crashing due to unexpected errors
            print(f"Error in expiration_worker: {e}")