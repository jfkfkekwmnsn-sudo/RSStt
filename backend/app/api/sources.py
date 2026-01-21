from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_admin, require_analyst
from app.models.user import User
from app.schemas.source import (
    SourceCreate, SourceUpdate, SourceResponse, SourceListItem,
    SourceRunResponse, FetchNowResponse
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.source_service import SourceService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SourceListItem])
async def list_sources(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """List all sources with pagination"""
    service = SourceService(db)
    sources, total = await service.list_sources(
        page=page,
        per_page=per_page,
        is_active=is_active,
        type=type,
        search=search
    )
    
    return PaginatedResponse.create(
        items=sources,
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new source"""
    service = SourceService(db)
    source = await service.create_source(data, current_user.id)
    return source


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get source by ID"""
    service = SourceService(db)
    source = await service.get_source(source_id)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    data: SourceUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update source"""
    service = SourceService(db)
    source = await service.update_source(source_id, data, current_user.id)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    return source


@router.delete("/{source_id}", response_model=MessageResponse)
async def delete_source(
    source_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete (archive) source"""
    service = SourceService(db)
    success = await service.delete_source(source_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    return MessageResponse(message="Source deleted successfully")


@router.post("/{source_id}/fetch-now", response_model=FetchNowResponse)
async def fetch_source_now(
    source_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger immediate fetch for source"""
    service = SourceService(db)
    result = await service.fetch_now(source_id, current_user.id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return FetchNowResponse(**result)


@router.get("/{source_id}/runs", response_model=List[SourceRunResponse])
async def get_source_runs(
    source_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get source fetch history"""
    service = SourceService(db)
    runs = await service.get_runs(source_id, limit)
    return runs
