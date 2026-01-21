from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_analyst
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.ai_service import AIService
from app.schemas.analytics import (
    AnalyticsSummaryResponse, EditorPerformanceResponse, SourceHealthResponse
)

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics summary"""
    service = AnalyticsService(db)
    return await service.get_full_summary(date_from, date_to)


@router.get("/categories")
async def get_category_analytics(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get category statistics"""
    service = AnalyticsService(db)
    return await service.get_category_stats(date_from, date_to)


@router.get("/sources")
async def get_source_analytics(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get source statistics"""
    service = AnalyticsService(db)
    return await service.get_source_stats(date_from, date_to, limit)


@router.get("/editors", response_model=EditorPerformanceResponse)
async def get_editor_performance(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get editor/moderator performance"""
    service = AnalyticsService(db)
    editors = await service.get_editor_stats(date_from, date_to)
    
    return EditorPerformanceResponse(
        editors=editors,
        period_start=date_from or (date.today() - timedelta(days=30)),
        period_end=date_to or date.today()
    )


@router.get("/publishing")
async def get_publishing_analytics(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get publishing statistics"""
    service = AnalyticsService(db)
    return await service.get_publishing_stats(date_from, date_to)


@router.get("/ai-usage")
async def get_ai_usage(
    current_user: User = Depends(require_analyst),
    db: AsyncSession = Depends(get_db)
):
    """Get AI usage statistics"""
    service = AIService(db)
    return await service.get_usage_stats()


from datetime import timedelta
