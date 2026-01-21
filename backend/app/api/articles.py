from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from app.api.deps import get_db, get_current_user, require_editor, require_analyst
from app.models.user import User
from app.models.article import ArticleStatus
from app.schemas.article import (
    ArticleResponse, ArticleListResponse, ArticleDetailResponse,
    ArticleUpdate, ArticleApproveRequest, ArticleRejectRequest,
    ArticleScheduleRequest, ArticleBulkActionRequest, ArticleBulkActionResponse,
    ArticleVersionResponse, ArticlePreviewRequest, ArticlePreviewResponse,
    ArticleFilterParams
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.article_service import ArticleService
from app.services.moderation_service import ModerationService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ArticleListResponse])
async def list_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[List[ArticleStatus]] = Query(None),
    category: Optional[str] = None,
    source_id: Optional[UUID] = None,
    has_image: Optional[bool] = None,
    ai_used: Optional[bool] = None,
    min_quality: Optional[float] = Query(None, ge=0, le=1),
    min_priority: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """List articles with filters and pagination"""
    service = ArticleService(db)
    
    filters = ArticleFilterParams(
        status=status,
        category=category,
        source_id=source_id,
        has_image=has_image,
        ai_used=ai_used,
        min_quality=min_quality,
        min_priority=min_priority,
        date_from=date_from,
        date_to=date_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    articles, total = await service.list_articles(
        filters=filters,
        page=page,
        per_page=per_page
    )
    
    return PaginatedResponse.create(
        items=articles,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/queue", response_model=PaginatedResponse[ArticleListResponse])
async def get_moderation_queue(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    priority: Optional[str] = Query(None, description="high, medium, low"),
    category: Optional[str] = None,
    source_id: Optional[UUID] = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Get articles in moderation queue"""
    service = ArticleService(db)
    
    articles, total = await service.get_moderation_queue(
        page=page,
        per_page=per_page,
        priority=priority,
        category=category,
        source_id=source_id
    )
    
    return PaginatedResponse.create(
        items=articles,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article(
    article_id: UUID,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get article details"""
    service = ArticleService(db)
    article = await service.get_article_detail(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    return article


@router.patch("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    data: ArticleUpdate,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Update article content"""
    service = ArticleService(db)
    article = await service.update_article(
        article_id=article_id,
        data=data,
        user_id=current_user.id
    )
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    return article


@router.post("/{article_id}/approve", response_model=MessageResponse)
async def approve_article(
    article_id: UUID,
    data: ArticleApproveRequest,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Approve article for publishing"""
    moderation_service = ModerationService(db)
    
    result = await moderation_service.approve_article(
        article_id=article_id,
        user_id=current_user.id,
        target_id=data.target_id,
        schedule_at=data.schedule_at,
        use_ai_rewrite=data.use_ai_rewrite
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return MessageResponse(message=result["message"])


@router.post("/{article_id}/reject", response_model=MessageResponse)
async def reject_article(
    article_id: UUID,
    data: ArticleRejectRequest,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Reject article"""
    moderation_service = ModerationService(db)
    
    result = await moderation_service.reject_article(
        article_id=article_id,
        user_id=current_user.id,
        reason=data.reason
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return MessageResponse(message=result["message"])


@router.post("/{article_id}/schedule", response_model=MessageResponse)
async def schedule_article(
    article_id: UUID,
    data: ArticleScheduleRequest,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Schedule article for future publishing"""
    moderation_service = ModerationService(db)
    
    result = await moderation_service.schedule_article(
        article_id=article_id,
        user_id=current_user.id,
        scheduled_at=data.scheduled_at,
        target_id=data.target_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return MessageResponse(message=result["message"])


@router.post("/{article_id}/publish", response_model=MessageResponse)
async def publish_now(
    article_id: UUID,
    target_id: Optional[UUID] = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Publish article immediately"""
    moderation_service = ModerationService(db)
    
    result = await moderation_service.publish_now(
        article_id=article_id,
        user_id=current_user.id,
        target_id=target_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return MessageResponse(message=result["message"])


@router.post("/{article_id}/retry", response_model=MessageResponse)
async def retry_publish(
    article_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Retry failed publishing"""
    moderation_service = ModerationService(db)
    
    result = await moderation_service.retry_publish(
        article_id=article_id,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return MessageResponse(message=result["message"])


@router.get("/{article_id}/versions", response_model=List[ArticleVersionResponse])
async def get_article_versions(
    article_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Get article version history"""
    service = ArticleService(db)
    versions = await service.get_versions(article_id)
    return versions


@router.post("/{article_id}/versions/{version_id}/restore", response_model=ArticleResponse)
async def restore_article_version(
    article_id: UUID,
    version_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Restore article to a specific version"""
    service = ArticleService(db)
    article = await service.restore_version(
        article_id=article_id,
        version_id=version_id,
        user_id=current_user.id
    )
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article or version not found"
        )
    
    return article


@router.post("/{article_id}/preview", response_model=ArticlePreviewResponse)
async def preview_article(
    article_id: UUID,
    data: ArticlePreviewRequest,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Preview how article will look when published"""
    service = ArticleService(db)
    preview = await service.generate_preview(
        article_id=article_id,
        template_id=data.template_id,
        target_id=data.target_id
    )
    
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    return preview


@router.post("/{article_id}/ai/rewrite", response_model=ArticleResponse)
async def ai_rewrite_article(
    article_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Apply AI rewriting to article"""
    service = ArticleService(db)
    article = await service.apply_ai_rewrite(
        article_id=article_id,
        user_id=current_user.id
    )
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI rewriting failed"
        )
    
    return article


@router.post("/bulk/approve", response_model=ArticleBulkActionResponse)
async def bulk_approve_articles(
    data: ArticleBulkActionRequest,
    target_id: Optional[UUID] = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Bulk approve multiple articles"""
    moderation_service = ModerationService(db)
    result = await moderation_service.bulk_approve(
        article_ids=data.article_ids,
        user_id=current_user.id,
        target_id=target_id
    )
    return result


@router.post("/bulk/reject", response_model=ArticleBulkActionResponse)
async def bulk_reject_articles(
    data: ArticleBulkActionRequest,
    reason: Optional[str] = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Bulk reject multiple articles"""
    moderation_service = ModerationService(db)
    result = await moderation_service.bulk_reject(
        article_ids=data.article_ids,
        user_id=current_user.id,
        reason=reason
    )
    return result
