from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus, ArticleVersion
from app.models.source import Source
from app.models.user import User
from app.schemas.article import ArticleUpdate, ArticleFilterParams, ArticleListResponse, ArticleDetailResponse
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction
import structlog

logger = structlog.get_logger()


class ArticleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)
    
    async def get_article(self, article_id: UUID) -> Optional[Article]:
        """Get article by ID"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_article_by_token(self, token: str) -> Optional[Article]:
        """Get article by public token"""
        query = select(Article).where(Article.token == token)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_article_detail(self, article_id: UUID) -> Optional[ArticleDetailResponse]:
        """Get article with full details"""
        query = select(Article).options(
            selectinload(Article.source),
            selectinload(Article.moderator)
        ).where(Article.id == article_id)
        
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return None
        
        # Get similar articles
        similar_articles = []
        if article.similar_to_id:
            similar_query = select(Article).where(Article.id == article.similar_to_id)
            similar_result = await self.db.execute(similar_query)
            similar = similar_result.scalar_one_or_none()
            if similar:
                similar_articles.append(similar)
        
        # Also find articles similar to this one
        reverse_similar_query = select(Article).where(
            Article.similar_to_id == article.id
        ).limit(5)
        reverse_result = await self.db.execute(reverse_similar_query)
        similar_articles.extend(reverse_result.scalars().all())
        
        # Get versions count
        versions_query = select(func.count(ArticleVersion.id)).where(
            ArticleVersion.article_id == article.id
        )
        versions_result = await self.db.execute(versions_query)
        versions_count = versions_result.scalar()
        
        return ArticleDetailResponse(
            id=article.id,
            token=article.token,
            project_id=article.project_id,
            source_id=article.source_id,
            source_name=article.source.name if article.source else None,
            url=article.url,
            title=article.title,
            description=article.description,
            content_clean=article.content_clean,
            pub_date=article.pub_date,
            category=article.category,
            tags=article.tags,
            images=article.images,
            main_image_url=article.main_image_url,
            quality_score=article.quality_score,
            quality_factors=article.quality_factors,
            priority_score=article.priority_score,
            priority_factors=article.priority_factors,
            status=article.status,
            batch_id=article.batch_id,
            ai_used=article.ai_used,
            ai_metadata=article.ai_metadata,
            moderated_at=article.moderated_at,
            moderator_id=article.moderator_id,
            moderator_name=article.moderator.username if article.moderator else None,
            rejection_reason=article.rejection_reason,
            published_at=article.published_at,
            scheduled_at=article.scheduled_at,
            published_target_id=article.published_target_id,
            published_external_id=article.published_external_id,
            similar_to_id=article.similar_to_id,
            similarity_score=article.similarity_score,
            similar_articles=[
                ArticleListResponse(
                    id=a.id,
                    token=a.token,
                    title=a.title,
                    category=a.category,
                    source_id=a.source_id,
                    status=a.status,
                    quality_score=a.quality_score,
                    priority_score=a.priority_score,
                    has_image=bool(a.main_image_url),
                    ai_used=a.ai_used,
                    pub_date=a.pub_date,
                    created_at=a.created_at
                ) for a in similar_articles
            ],
            versions_count=versions_count,
            created_at=article.created_at,
            updated_at=article.updated_at
        )
    
    async def list_articles(
        self,
        filters: ArticleFilterParams,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[ArticleListResponse], int]:
        """List articles with filters"""
        query = select(Article).options(selectinload(Article.source))
        
        # Apply filters
        conditions = []
        
        if filters.status:
            conditions.append(Article.status.in_(filters.status))
        
        if filters.category:
            conditions.append(Article.category == filters.category)
        
        if filters.source_id:
            conditions.append(Article.source_id == filters.source_id)
        
        if filters.has_image is not None:
            if filters.has_image:
                conditions.append(Article.main_image_url != None)
            else:
                conditions.append(Article.main_image_url == None)
        
        if filters.ai_used is not None:
            conditions.append(Article.ai_used == filters.ai_used)
        
        if filters.min_quality is not None:
            conditions.append(Article.quality_score >= filters.min_quality)
        
        if filters.max_quality is not None:
            conditions.append(Article.quality_score <= filters.max_quality)
        
        if filters.min_priority is not None:
            conditions.append(Article.priority_score >= filters.min_priority)
        
        if filters.date_from:
            conditions.append(Article.created_at >= filters.date_from)
        
        if filters.date_to:
            conditions.append(Article.created_at <= filters.date_to)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Article.title.ilike(search_term),
                    Article.content_clean.ilike(search_term)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count(Article.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Sorting
        sort_column = getattr(Article, filters.sort_by, Article.created_at)
        if filters.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        # Convert to response
        items = [
            ArticleListResponse(
                id=a.id,
                token=a.token,
                title=a.title,
                category=a.category,
                source_id=a.source_id,
                source_name=a.source.name if a.source else None,
                status=a.status,
                quality_score=a.quality_score,
                priority_score=a.priority_score,
                has_image=bool(a.main_image_url),
                ai_used=a.ai_used,
                pub_date=a.pub_date,
                created_at=a.created_at
            ) for a in articles
        ]
        
        return items, total
    
    async def get_moderation_queue(
        self,
        page: int = 1,
        per_page: int = 20,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        source_id: Optional[UUID] = None
    ) -> Tuple[List[Article], int]:
        """Get articles pending moderation"""
        query = select(Article).options(selectinload(Article.source)).where(
            Article.status.in_([ArticleStatus.PENDING, ArticleStatus.NEEDS_REVIEW])
        )
        
        conditions = []
        
        if category:
            conditions.append(Article.category == category)
        
        if source_id:
            conditions.append(Article.source_id == source_id)
        
        if priority:
            if priority == "high":
                conditions.append(Article.priority_score >= 70)
            elif priority == "medium":
                conditions.append(and_(Article.priority_score >= 40, Article.priority_score < 70))
            elif priority == "low":
                conditions.append(Article.priority_score < 40)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count
        count_query = select(func.count(Article.id)).where(
            Article.status.in_([ArticleStatus.PENDING, ArticleStatus.NEEDS_REVIEW])
        )
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Order by priority desc, then by created_at
        query = query.order_by(
            desc(Article.priority_score),
            asc(Article.created_at)
        )
        
        # Pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        return articles, total
    
    async def update_article(
        self,
        article_id: UUID,
        data: ArticleUpdate,
        user_id: UUID
    ) -> Optional[Article]:
        """Update article content"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return None
        
        # Create version before update
        await self._create_version(article, user_id, "Manual edit")
        
        # Store before state
        before_state = {
            "title": article.title,
            "content_clean": article.content_clean,
            "category": article.category,
            "tags": article.tags
        }
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(article, field):
                setattr(article, field, value)
        
        await self.db.commit()
        
        # Audit log
        await self.audit.log(
            action=AuditAction.ARTICLE_EDITED,
            entity_type="article",
            entity_id=article.id,
            actor_id=user_id,
            actor_type="user",
            before_state=before_state,
            after_state=update_data
        )
        
        logger.info("Article updated", article_id=str(article_id), user_id=str(user_id))
        
        return article
    
    async def _create_version(
        self,
        article: Article,
        user_id: Optional[UUID],
        change_summary: Optional[str] = None
    ):
        """Create article version snapshot"""
        # Get current version number
        version_query = select(func.max(ArticleVersion.version_number)).where(
            ArticleVersion.article_id == article.id
        )
        version_result = await self.db.execute(version_query)
        max_version = version_result.scalar() or 0
        
        version = ArticleVersion(
            article_id=article.id,
            version_number=max_version + 1,
            title=article.title,
            content_clean=article.content_clean,
            category=article.category,
            tags=article.tags,
            main_image_url=article.main_image_url,
            created_by_id=user_id,
            change_summary=change_summary
        )
        self.db.add(version)
    
    async def get_versions(self, article_id: UUID) -> List[ArticleVersion]:
        """Get article version history"""
        query = select(ArticleVersion).where(
            ArticleVersion.article_id == article_id
        ).order_by(desc(ArticleVersion.version_number))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def restore_version(
        self,
        article_id: UUID,
        version_id: UUID,
        user_id: UUID
    ) -> Optional[Article]:
        """Restore article to specific version"""
        # Get version
        version_query = select(ArticleVersion).where(
            and_(
                ArticleVersion.id == version_id,
                ArticleVersion.article_id == article_id
            )
        )
        version_result = await self.db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            return None
        
        # Get article
        article_query = select(Article).where(Article.id == article_id)
        article_result = await self.db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            return None
        
        # Create version of current state
        await self._create_version(article, user_id, f"Before restore to v{version.version_number}")
        
        # Restore
        article.title = version.title
        article.content_clean = version.content_clean
        article.category = version.category
        article.tags = version.tags
        article.main_image_url = version.main_image_url
        
        await self.db.commit()
        
        logger.info(
            "Article restored",
            article_id=str(article_id),
            version=version.version_number,
            user_id=str(user_id)
        )
        
        return article
    
    async def generate_preview(
        self,
        article_id: UUID,
        template_id: Optional[UUID] = None,
        target_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate preview of article as it will be published"""
        from app.services.template_service import TemplateService
        template_service = TemplateService(self.db)
        
        return await template_service.render_for_article(
            article_id=article_id,
            template_id=template_id,
            target_id=target_id
        )
    
    async def apply_ai_rewrite(
        self,
        article_id: UUID,
        user_id: UUID
    ) -> Optional[Article]:
        """Apply AI rewrite to article"""
        from app.services.ai_service import AIService
        ai_service = AIService(self.db)
        
        result = await ai_service.rewrite_article(article_id, user_id)
        
        if result.get("success"):
            return await self.get_article(article_id)
        
        return None