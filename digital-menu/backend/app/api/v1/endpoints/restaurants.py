from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from slugify import slugify

from app.db.session import get_db
from app.database_models import User, Restaurant, Branch, UserRole
from app.schemas import RestaurantCreate, RestaurantUpdate, RestaurantOut, BranchCreate, BranchOut
from app.api.deps import get_current_user, require_manager_or_above, require_super_admin

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=List[RestaurantOut])
async def list_restaurants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Restaurant)
    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.where(Restaurant.id == current_user.restaurant_id)
    result = await db.execute(query)
    return [RestaurantOut.model_validate(r) for r in result.scalars().all()]


@router.post("", response_model=RestaurantOut, status_code=201)
async def create_restaurant(
    body: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    slug = body.slug or slugify(body.name)
    existing = await db.execute(select(Restaurant).where(Restaurant.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Restaurant slug already exists")

    restaurant = Restaurant(name=body.name, slug=slug, logo_url=body.logo_url)
    db.add(restaurant)
    await db.commit()
    await db.refresh(restaurant)
    return RestaurantOut.model_validate(restaurant)


@router.get("/{restaurant_id}", response_model=RestaurantOut)
async def get_restaurant(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return RestaurantOut.model_validate(r)


@router.patch("/{restaurant_id}", response_model=RestaurantOut)
async def update_restaurant(
    restaurant_id: int,
    body: RestaurantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(r, field, value)
    await db.commit()
    await db.refresh(r)
    return RestaurantOut.model_validate(r)


# ─── Branches ─────────────────────────────────────────────────────────────────

# @router.get("/{restaurant_id}/branches", response_model=List[BranchOut])
# async def list_branches(
#     restaurant_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     result = await db.execute(
#         select(Branch).where(Branch.restaurant_id == restaurant_id)
#     )
#     return [BranchOut.model_validate(b) for b in result.scalars().all()]


# @router.post("/{restaurant_id}/branches", response_model=BranchOut, status_code=201)
# async def create_branch(
#     restaurant_id: int,
#     body: BranchCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(require_manager_or_above),
# ):
#     branch = Branch(restaurant_id=restaurant_id, **body.model_dump())
#     db.add(branch)
#     await db.commit()
#     await db.refresh(branch)
#     return BranchOut.model_validate(branch)
