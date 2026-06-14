from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.db.redis import cache_delete_pattern
from app.database_models import User, Menutemplates, MenutemplatesItems, MenuItem, UserRole
from app.schemas import (
    TemplateOut,
    TemplateSaveRequest,
)
from app.api.deps import get_current_user, require_manager_or_above


router = APIRouter(prefix="/templates", tags=["templates"])


def _assert_restaurant(user: User, restaurant_id: int):
    """Ensure non-super-admins can only touch their own restaurant."""
    if user.role != UserRole.SUPER_ADMIN and user.restaurant_id != restaurant_id:
        raise HTTPException(status_code=403, detail="Access denied to this restaurant")


# ─── List all templates for a restaurant ─────────────────────────────────────

@router.get("/restaurant/{restaurant_id}", response_model=List[TemplateOut])
async def list_templates(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_restaurant(current_user, restaurant_id)

    result = await db.execute(
        select(Menutemplates)
        .where(Menutemplates.restaurant_id == restaurant_id)
        .options(
            selectinload(Menutemplates.items).selectinload(MenutemplatesItems.menu_item)
        )
        .order_by(Menutemplates.id)
    )
    templates = result.scalars().all()
    return [TemplateOut.model_validate(t) for t in templates]


# ─── Create / Save a template with items ─────────────────────────────────────

@router.post("/restaurant/{restaurant_id}", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    restaurant_id: int,
    body: TemplateSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    _assert_restaurant(current_user, restaurant_id)

    # Validate all item IDs exist
    print(body.items)
    if body.items:
        item_ids = [i.item_id for i in body.items]
        result = await db.execute(
            select(MenuItem).where(MenuItem.id.in_(item_ids))
        )
        found = {m.id for m in result.scalars().all()}
        missing = set(item_ids) - found
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Menu items not found: {sorted(missing)}"
            )

    # Create template
    template = Menutemplates(
        restaurant_id=restaurant_id,
        name=body.name,
        name_local=body.name_local,
        price=0.0,
        is_active=False,
    )
    db.add(template)
    await db.flush()  # get template.id before adding children

    # Add template items
    for entry in body.items:
        db.add(MenutemplatesItems(
            template_id=template.id,
            items_id=entry.item_id,
            duration_second=entry.duration_seconds,
        ))

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Menutemplates)
        .where(Menutemplates.id == template.id)
        .options(
            selectinload(Menutemplates.items).selectinload(MenutemplatesItems.menu_item)
        )
    )
    template = result.scalar_one()
    return TemplateOut.model_validate(template)


# ─── Activate a template (deactivate all others for the same restaurant) ──────

@router.patch("/{template_id}/activate", response_model=TemplateOut)
async def activate_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    # Fetch the target template
    result = await db.execute(
        select(Menutemplates)
        .where(Menutemplates.id == template_id)
        .options(
            selectinload(Menutemplates.items).selectinload(MenutemplatesItems.menu_item)
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    _assert_restaurant(current_user, template.restaurant_id)

    # Deactivate all templates for this restaurant
    await db.execute(
        update(Menutemplates)
        .where(Menutemplates.restaurant_id == template.restaurant_id)
        .values(is_active=False)
    )

    # Activate this one
    template.is_active = True
    await db.commit()
    await db.refresh(template)

    # Invalidate menu cache so TV displays pick up changes
    await cache_delete_pattern(f"menu:{template.restaurant_id}:*")

    # Reload with relationships
    result = await db.execute(
        select(Menutemplates)
        .where(Menutemplates.id == template_id)
        .options(
            selectinload(Menutemplates.items).selectinload(MenutemplatesItems.menu_item)
        )
    )
    template = result.scalar_one()
    return TemplateOut.model_validate(template)


# ─── Delete a template ────────────────────────────────────────────────────────

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(
        select(Menutemplates).where(Menutemplates.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    _assert_restaurant(current_user, template.restaurant_id)

    await db.delete(template)
    await db.commit()