from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.models.publish_target import PublishTarget
from app.schemas.publish_target import (
    PublishTargetCreate, PublishTargetUpdate, PublishTargetResponse
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("", response_model=List[PublishTargetResponse])
async def list_targets(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all publish targets"""
    query = select(PublishTarget).order_by(PublishTarget.name)
    result = await db.execute(query)
    targets = result.scalars().all()
    return targets


@router.post("", response_model=PublishTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    data: PublishTargetCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new publish target"""
    target = PublishTarget(
        name=data.name,
        type=data.type,
        telegram_chat_id=data.telegram_chat_id,
        telegram_chat_username=data.telegram_chat_username,
        settings=data.settings.model_dump() if data.settings else None,
        is_active=data.is_active
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/{target_id}", response_model=PublishTargetResponse)
async def get_target(
    target_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get target by ID"""
    query = select(PublishTarget).where(PublishTarget.id == target_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return target


@router.patch("/{target_id}", response_model=PublishTargetResponse)
async def update_target(
    target_id: UUID,
    data: PublishTargetUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update target"""
    query = select(PublishTarget).where(PublishTarget.id == target_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "settings" in update_data and update_data["settings"]:
        update_data["settings"] = update_data["settings"].model_dump() \
            if hasattr(update_data["settings"], "model_dump") \
            else update_data["settings"]
    
    for field, value in update_data.items():
        if hasattr(target, field):
            setattr(target, field, value)
    
    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/{target_id}", response_model=MessageResponse)
async def delete_target(
    target_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete target"""
    query = select(PublishTarget).where(PublishTarget.id == target_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    await db.delete(target)
    await db.commit()
    return MessageResponse(message="Target deleted")