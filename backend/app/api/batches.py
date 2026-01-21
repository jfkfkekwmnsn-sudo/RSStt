from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db, require_editor
from app.models.user import User
from app.models.batch import Batch, BatchStatus
from app.schemas.batch import BatchResponse, BatchDetailResponse, BatchActionResponse
from app.services.moderation_service import ModerationService
from app.services.batch_service import BatchService

router = APIRouter()


@router.get("", response_model=List[BatchResponse])
async def list_batches(
    status: BatchStatus = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """List batches"""
    query = select(Batch)
    if status:
        query = query.where(Batch.status == status)
    query = query.order_by(Batch.created_at.desc()).limit(50)
    
    result = await db.execute(query)
    batches = result.scalars().all()
    return batches


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Get batch with articles"""
    service = BatchService(db)
    batch = await service.get_batch(batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    articles = await service.get_batch_articles(batch_id)
    
    return BatchDetailResponse(
        **batch.__dict__,
        articles=articles
    )


@router.post("/{batch_id}/approve-all", response_model=BatchActionResponse)
async def approve_batch(
    batch_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Approve all articles in batch"""
    service = ModerationService(db)
    result = await service.approve_batch(batch_id, current_user.id)
    
    return BatchActionResponse(
        success=True,
        message=result.get("message", "Batch approved"),
        approved_count=result.get("approved_count", 0),
        rejected_count=0
    )


@router.post("/{batch_id}/reject-all", response_model=BatchActionResponse)
async def reject_batch(
    batch_id: UUID,
    reason: str = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Reject all articles in batch"""
    service = ModerationService(db)
    result = await service.reject_batch(batch_id, current_user.id, reason)
    
    return BatchActionResponse(
        success=True,
        message=result.get("message", "Batch rejected"),
        approved_count=0,
        rejected_count=result.get("rejected_count", 0)
    )
