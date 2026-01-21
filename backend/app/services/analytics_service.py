from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case

from app.models.article import Article, ArticleStatus
from app.models.source import Source
from app.models.user import User
from app.models.publish_job import PublishJob, PublishJobStatus
from app.schemas.analytics import (
    SummaryStats, CategoryStats, SourceStats, EditorStats,
    TimeSeriesPoint, AnalyticsSummaryResponse
)
import structlog

logger = structlog.get_logger()


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_summary_stats(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary statistics"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        # Convert to datetime
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        
        # Total articles
        total_query = select(func.count(Article.id)).where(
            Article.created_at.between(start, end)
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()
        
        # By status
        status_query = select(
            Article.status,
            func.count(Article.id)
        ).where(
            Article.created_at.between(start, end)
        ).group_by(Article.status)
        
        status_result = await self.db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result}
        
        pending = status_counts.get(ArticleStatus.PENDING, 0) + status_counts.get(ArticleStatus.NEEDS_REVIEW, 0)
        approved = status_counts.get(ArticleStatus.APPROVED, 0) + status_counts.get(ArticleStatus.SCHEDULED, 0)
        rejected = status_counts.get(ArticleStatus.REJECTED, 0)
        published = status_counts.get(ArticleStatus.PUBLISHED, 0)
        
        # Approval rate
        moderated = approved + rejected
        approval_rate = approved / moderated if moderated > 0 else 0
        
        # Average processing time
        avg_time_query = select(
            func.avg(
                func.extract('epoch', Article.moderated_at - Article.created_at) / 60
            )
        ).where(
            and_(
                Article.created_at.between(start, end),
                Article.moderated_at != None
            )
        )
        avg_time_result = await self.db.execute(avg_time_query)
        avg_processing_time = avg_time_result.scalar()
        
        # Today's stats
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_query = select(func.count(Article.id)).where(
            Article.created_at >= today_start
        )
        today_result = await self.db.execute(today_query)
        articles_today = today_result.scalar()
        
        # This week
        week_start = datetime.combine(date.today() - timedelta(days=7), datetime.min.time())
        week_query = select(func.count(Article.id)).where(
            Article.created_at >= week_start
        )
        week_result = await self.db.execute(week_query)
        articles_week = week_result.scalar()
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "published": published,
            "approval_rate": approval_rate,
            "avg_processing_time_minutes": round(avg_processing_time, 1) if avg_processing_time else None,
            "today": {
                "incoming": articles_today
            },
            "articles_today": articles_today,
            "articles_this_week": articles_week
        }
    
    async def get_category_stats(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[CategoryStats]:
        """Get statistics by category"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        
        query = select(
            Article.category,
            func.count(Article.id).label('total'),
            func.sum(case((Article.status.in_([ArticleStatus.APPROVED, ArticleStatus.SCHEDULED, ArticleStatus.PUBLISHED]), 1), else_=0)).label('approved'),
            func.sum(case((Article.status == ArticleStatus.REJECTED, 1), else_=0)).label('rejected'),
            func.sum(case((Article.status == ArticleStatus.PUBLISHED, 1), else_=0)).label('published')
        ).where(
            Article.created_at.between(start, end)
        ).group_by(Article.category).order_by(func.count(Article.id).desc())
        
        result = await self.db.execute(query)
        rows = result.all()
        
        stats = []
        for row in rows:
            category = row.category or "Без категории"
            total = row.total
            approved = row.approved or 0
            rejected = row.rejected or 0
            published = row.published or 0
            
            moderated = approved + rejected
            approval_rate = approved / moderated if moderated > 0 else 0
            
            stats.append(CategoryStats(
                category=category,
                total=total,
                approved=approved,
                rejected=rejected,
                published=published,
                approval_rate=approval_rate
            ))
        
        return stats
    
    async def get_source_stats(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 20
    ) -> List[SourceStats]:
        """Get statistics by source"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        
        query = select(
            Source.id,
            Source.name,
            Source.reputation_score,
            func.count(Article.id).label('total'),
            func.sum(case((Article.status.in_([ArticleStatus.APPROVED, ArticleStatus.SCHEDULED, ArticleStatus.PUBLISHED]), 1), else_=0)).label('approved'),
            func.sum(case((Article.status == ArticleStatus.REJECTED, 1), else_=0)).label('rejected'),
            func.avg(Article.quality_score).label('avg_quality')
        ).join(
            Article, Source.id == Article.source_id
        ).where(
            Article.created_at.between(start, end)
        ).group_by(
            Source.id, Source.name, Source.reputation_score
        ).order_by(
            func.count(Article.id).desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        stats = []
        for row in rows:
            total = row.total
            approved = row.approved or 0
            rejected = row.rejected or 0
            
            moderated = approved + rejected
            approval_rate = approved / moderated if moderated > 0 else 0
            
            stats.append(SourceStats(
                source_id=str(row.id),
                source_name=row.name,
                total=total,
                approved=approved,
                rejected=rejected,
                approval_rate=approval_rate,
                avg_quality=round(row.avg_quality or 0, 2),
                reputation_score=round(row.reputation_score or 0, 2)
            ))
        
        return stats
    
    async def get_editor_stats(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[EditorStats]:
        """Get statistics by editor/moderator"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        
        query = select(
            User.id,
            User.username,
            func.count(Article.id).label('total'),
            func.sum(case((Article.status.in_([ArticleStatus.APPROVED, ArticleStatus.SCHEDULED, ArticleStatus.PUBLISHED]), 1), else_=0)).label('approved'),
            func.sum(case((Article.status == ArticleStatus.REJECTED, 1), else_=0)).label('rejected'),
            func.avg(
                func.extract('epoch', Article.moderated_at - Article.created_at) / 60
            ).label('avg_time')
        ).join(
            Article, User.id == Article.moderator_id
        ).where(
            Article.moderated_at.between(start, end)
        ).group_by(
            User.id, User.username
        ).order_by(
            func.count(Article.id).desc()
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        stats = []
        for row in rows:
            stats.append(EditorStats(
                user_id=str(row.id),
                username=row.username,
                total_moderated=row.total,
                approved=row.approved or 0,
                rejected=row.rejected or 0,
                avg_processing_time_minutes=round(row.avg_time or 0, 1)
            ))
        
        return stats
    
    async def get_articles_by_day(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[TimeSeriesPoint]:
        """Get article count by day"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        
        query = select(
            func.date(Article.created_at).label('day'),
            func.count(Article.id).label('count')
        ).where(
            Article.created_at.between(start, end)
        ).group_by(
            func.date(Article.created_at)
        ).order_by('day')
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Fill in missing days
        points = []
        current = date_from
        row_dict = {row.day: row.count for row in rows}
        
        while current <= date_to:
            points.append(TimeSeriesPoint(
                date=current,
                count=row_dict.get(current, 0)
            ))
            current += timedelta(days=1)
        
        return points
    
    async def get_full_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> AnalyticsSummaryResponse:
        """Get full analytics summary"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        summary = await self.get_summary_stats(date_from, date_to)
        categories = await self.get_category_stats(date_from, date_to)
        sources = await self.get_source_stats(date_from, date_to, limit=10)
        by_day = await self.get_articles_by_day(date_from, date_to)
        
        return AnalyticsSummaryResponse(
            summary=SummaryStats(**summary),
            categories=categories,
            top_sources=sources,
            articles_by_day=by_day,
            period_start=date_from,
            period_end=date_to
        )
    
    async def get_publishing_stats(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get publishing statistics"""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        
        # Total jobs
        total_query = select(func.count(PublishJob.id)).where(
            PublishJob.created_at.between(start, end)
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()
        
        # By status
        status_query = select(
            PublishJob.status,
            func.count(PublishJob.id)
        ).where(
            PublishJob.created_at.between(start, end)
        ).group_by(PublishJob.status)
        
        status_result = await self.db.execute(status_query)
        status_counts = {row[0].value: row[1] for row in status_result}
        
        # Success rate
        published = status_counts.get('published', 0)
        failed = status_counts.get('failed', 0)
        success_rate = published / (published + failed) if (published + failed) > 0 else 0
        
        return {
            "total_jobs": total,
            "by_status": status_counts,
            "success_rate": success_rate
        }
