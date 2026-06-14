from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import get_db
from app.database_models import User, Device, Branch, UserRole
from app.schemas import DeviceCreate, DeviceUpdate, DeviceOut
from app.api.deps import get_current_user, require_manager_or_above

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=List[DeviceOut])
async def list_devices(
    branch_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Device).join(Branch)
    if branch_id:
        query = query.where(Device.branch_id == branch_id)
    elif current_user.role != UserRole.SUPER_ADMIN:
        # Filter to branches within user's restaurant
        query = query.where(Branch.restaurant_id == current_user.restaurant_id)
    result = await db.execute(query)
    return [DeviceOut.model_validate(d) for d in result.scalars().all()]


def _generate_fake_mac() -> str:
    return ":".join(uuid4().hex[i:i+2].upper() for i in range(0, 12, 2))


@router.post("", response_model=DeviceOut, status_code=201)
async def register_device(
    body: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    # Verify branch exists
    branch_result = await db.execute(select(Branch).where(Branch.id == body.branch_id))
    branch = branch_result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    payload = body.model_dump(exclude_none=True)
    mac_address = payload.get('mac_address') or _generate_fake_mac()

    while True:
        existing = await db.execute(select(Device).where(Device.mac_address == mac_address))
        if not existing.scalar_one_or_none():
            break
        mac_address = _generate_fake_mac()

    payload['mac_address'] = mac_address

    device = Device(**payload)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DeviceOut.model_validate(device)


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await db.commit()
    await db.refresh(device)
    return DeviceOut.model_validate(device)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()


@router.post("/{device_id}/heartbeat", status_code=200)
async def device_heartbeat(
    device_id: int,
    mac_address: str,
    db: AsyncSession = Depends(get_db),
):
    """Called by TV app every 30s to indicate it's online."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.mac_address == mac_address)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or MAC mismatch")

    from app.database_models import DeviceStatus
    device.last_seen = datetime.now(timezone.utc)
    device.status = DeviceStatus.ACTIVE
    await db.commit()
    return {"status": "ok", "device_id": device_id}
