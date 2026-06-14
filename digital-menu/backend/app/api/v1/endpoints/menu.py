from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.redis import publish_menu_update, cache_delete_pattern
from app.database_models import User, MenuGroup, MenuSubGroup, MenuItem, UserRole
from app.schemas import (
    MenuGroupCreate, MenuGroupUpdate, MenuGroupOut, MenuGroupWithChildren,
    MenuSubGroupCreate, MenuSubGroupUpdate, MenuSubGroupOut, MenuSubGroupWithItems,
    MenuItemCreate, MenuItemUpdate, MenuItemOut,
    FullMenuResponse, RestaurantOut, ReorderItemsRequest
)
from app.api.deps import get_current_user, require_manager_or_above



router = APIRouter(prefix="/menu", tags=["menu"])


def _assert_restaurant(user: User, restaurant_id: int):
    if user.role != UserRole.SUPER_ADMIN and user.restaurant_id != restaurant_id:
        raise HTTPException(status_code=403, detail="Access denied to this restaurant")


# ─── Menu Groups ─────────────────────────────────────────────────────────────

@router.get("/restaurants/{restaurant_id}/groups", response_model=List[MenuGroupOut])
async def list_groups(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_restaurant(current_user, restaurant_id)
    result = await db.execute(
        select(MenuGroup)
        .where(MenuGroup.restaurant_id == restaurant_id)
        .order_by(MenuGroup.sequence)
    )
    return [MenuGroupOut.model_validate(g) for g in result.scalars().all()]


@router.post("/restaurants/{restaurant_id}/groups", response_model=MenuGroupOut, status_code=201)
async def create_group(
    restaurant_id: int,
    body: MenuGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    _assert_restaurant(current_user, restaurant_id)
    group = MenuGroup(restaurant_id=restaurant_id, **body.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    await cache_delete_pattern(f"menu:{restaurant_id}:*")
    return MenuGroupOut.model_validate(group)


@router.patch("/groups/{group_id}", response_model=MenuGroupOut)
async def update_group(
    group_id: int,
    body: MenuGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(MenuGroup).where(MenuGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _assert_restaurant(current_user, group.restaurant_id)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await db.commit()
    await db.refresh(group)
    await cache_delete_pattern(f"menu:{group.restaurant_id}:*")
    return MenuGroupOut.model_validate(group)


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(MenuGroup).where(MenuGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _assert_restaurant(current_user, group.restaurant_id)
    await db.delete(group)
    await db.commit()
    await cache_delete_pattern(f"menu:{group.restaurant_id}:*")


# ─── Sub Groups ───────────────────────────────────────────────────────────────

@router.get("/groups/{group_id}/subgroups", response_model=List[MenuSubGroupOut])
async def list_subgroups(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MenuSubGroup).where(MenuSubGroup.group_id == group_id).order_by(MenuSubGroup.sequence)
    )
    return [MenuSubGroupOut.model_validate(sg) for sg in result.scalars().all()]


@router.post("/groups/{group_id}/subgroups", response_model=MenuSubGroupOut, status_code=201)
async def create_subgroup(
    group_id: int,
    body: MenuSubGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    # Verify group exists
    result = await db.execute(select(MenuGroup).where(MenuGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _assert_restaurant(current_user, group.restaurant_id)

    subgroup = MenuSubGroup(group_id=group_id, **body.model_dump())
    db.add(subgroup)
    await db.commit()
    await db.refresh(subgroup)
    await cache_delete_pattern(f"menu:{group.restaurant_id}:*")
    return MenuSubGroupOut.model_validate(subgroup)


@router.patch("/subgroups/{subgroup_id}", response_model=MenuSubGroupOut)
async def update_subgroup(
    subgroup_id: int,
    body: MenuSubGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(
        select(MenuSubGroup).where(MenuSubGroup.id == subgroup_id).options(selectinload(MenuSubGroup.group))
    )
    sg = result.scalar_one_or_none()
    if not sg:
        raise HTTPException(status_code=404, detail="Sub-group not found")
    _assert_restaurant(current_user, sg.group.restaurant_id)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sg, field, value)
    await db.commit()
    await db.refresh(sg)
    return MenuSubGroupOut.model_validate(sg)


@router.delete("/subgroups/{subgroup_id}", status_code=204)
async def delete_subgroup(
    subgroup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(MenuSubGroup).where(MenuSubGroup.id == subgroup_id))
    sg = result.scalar_one_or_none()
    if not sg:
        raise HTTPException(status_code=404, detail="Sub-group not found")
    await db.delete(sg)
    await db.commit()


# ─── Menu Items ───────────────────────────────────────────────────────────────

@router.get("/subgroups/{subgroup_id}/items", response_model=List[MenuItemOut])
async def list_items(
    subgroup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MenuItem).where(MenuItem.sub_group_id == subgroup_id).order_by(MenuItem.sequence)
    )
    return [MenuItemOut.model_validate(i) for i in result.scalars().all()]


@router.post("/subgroups/{subgroup_id}/items", response_model=MenuItemOut, status_code=201)
async def create_item(
    subgroup_id: int,
    body: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    item = MenuItem(sub_group_id=subgroup_id, **body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return MenuItemOut.model_validate(item)


@router.patch("/items/{item_id}", response_model=MenuItemOut)
async def update_item(
    item_id: int,
    body: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return MenuItemOut.model_validate(item)


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()



# If user tries to rearrange the order of groups, subgroups and items 

@router.post('/reorder/groups')
async def reorder_groups(
    body: ReorderItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    for index, group_id in enumerate(body.ids):
        await db.execute(update(MenuGroup).where(MenuGroup.id == group_id).values(sequence= index))

    await db.commit()

# Invalidate cache for this restaurant
    if body.ids:
        result = await db.execute(select(MenuGroup.restaurant_id).where(MenuGroup.id == body.ids[0]))
        restaurant_id = result.scalar_one_or_none()
        if restaurant_id:
            await cache_delete_pattern(f"menu:{restaurant_id}:*")
            
    return {"message": "Categories reordered successfully"}


@router.post("/reorder/subgroups")
async def reorder_subgroups(
    body: ReorderItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    for index, sg_id in enumerate(body.ids):
        await db.execute(
            update(MenuSubGroup)
            .where(MenuSubGroup.id == sg_id)
            .values(sequence=index)
        )
    await db.commit()
    
    # Invalidate cache
    if body.ids:
        result = await db.execute(
            select(MenuGroup.restaurant_id)
            .join(MenuSubGroup, MenuSubGroup.group_id == MenuGroup.id)
            .where(MenuSubGroup.id == body.ids[0])
        )
        restaurant_id = result.scalar_one_or_none()
        if restaurant_id:
            await cache_delete_pattern(f"menu:{restaurant_id}:*")
            
    return {"message": "Sub-categories reordered successfully"}


@router.post("/reorder/items")
async def reorder_items(
    body: ReorderItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    for index, item_id in enumerate(body.ids):
        await db.execute(
            update(MenuItem)
            .where(MenuItem.id == item_id)
            .values(sequence=index)
        )
    await db.commit()
    
    # Invalidate cache
    if body.ids:
        result = await db.execute(
            select(MenuGroup.restaurant_id)
            .join(MenuSubGroup, MenuSubGroup.group_id == MenuGroup.id)
            .join(MenuItem, MenuItem.sub_group_id == MenuSubGroup.id)
            .where(MenuItem.id == body.ids[0])
        )
        restaurant_id = result.scalar_one_or_none()
        if restaurant_id:
            await cache_delete_pattern(f"menu:{restaurant_id}:*")
            
    return {"message": "Items reordered successfully"}















# ─── Full Menu (used by TV app + publish) ─────────────────────────────────────

@router.get("/restaurants/{restaurant_id}/full", response_model=FullMenuResponse)
async def get_full_menu(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the complete menu tree for a restaurant. Used by TV app."""
    from app.database_models import Restaurant
    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    groups_result = await db.execute(
        select(MenuGroup)
        .where(MenuGroup.restaurant_id == restaurant_id, MenuGroup.is_active == True)
        .options(
            selectinload(MenuGroup.sub_groups).selectinload(MenuSubGroup.items)
        )
        .order_by(MenuGroup.sequence)
    )
    groups = groups_result.scalars().unique().all()

    return FullMenuResponse(
        restaurant=RestaurantOut.model_validate(restaurant),
        groups=[MenuGroupWithChildren.model_validate(g) for g in groups],
        published_at=datetime.now(timezone.utc),
    )


@router.post("/restaurants/{restaurant_id}/publish", status_code=200)
async def publish_menu(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    """Instantly pushes the current menu to all connected TV devices via WebSocket."""
    _assert_restaurant(current_user, restaurant_id)
    await publish_menu_update(restaurant_id, {
        "event": "menu_published",
        "published_by": current_user.username,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    await cache_delete_pattern(f"menu:{restaurant_id}:*")
    return {"message": "Menu published to all connected TVs", "restaurant_id": restaurant_id}
