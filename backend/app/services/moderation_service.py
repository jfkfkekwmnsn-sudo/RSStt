from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.article import Article, ArticleStatus
from app.models.batch import Batch, BatchStatus
from app.models.publish_target import PublishTarget
from app.models.publish_job import PublishJob, PublishJobStatus
from app.services.audit_service import AuditService
from app.services.publishing_service import PublishingService
from app.models.audit_log import AuditAction
import structlog

logger = structlog.get_logger()


class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)
    
    async def approve_article(
        self,
        article_id: UUID,
        user_id: UUID,
        target_id: Optional[UUID] = None,
        schedule_at: Optional[datetime] = None,
        use_ai_rewrite: bool = False
    ) -> Dict[str, Any]:
        """Approve article for publishing"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "message": "Article not found"}
        
        if article.status not in [ArticleStatus.PENDING, ArticleStatus.NEEDS_REVIEW]:
            return {"success": False, "message": f"Cannot approve article with status {article.status.value}"}
        
        # Store previous state for audit
        before_state = {
            "status": article.status.value,
            "moderated_at": str(article.moderated_at) if article.moderated_at else None
        }
        
        # Apply AI rewrite if requested
        if use_ai_rewrite:
            from app.workers.tasks import ai_rewrite_task
            ai_rewrite_task.delay(str(article_id), str(user_id))
        
        # Update article status
        if schedule_at:
            article.status = ArticleStatus.SCHEDULED
            article.scheduled_at = schedule_at
        else:
            article.status = ArticleStatus.APPROVED
        
        article.moderated_at = datetime.utcnow()
        article.moderator_id = user_id
        
        # Get default target if not specified
        if not target_id:
            target_query = select(PublishTarget).where(
                PublishTarget.is_active == True
            ).limit(1)
            target_result = await self.db.execute(target_query)
            target = target_result.scalar_one_or_none()
            if target:
                target_id = target.id
        
        # Create publish job
        if target_id:
            job = PublishJob(
                article_id=article.id,
                target_id=target_id,
                status=PublishJobStatus.SCHEDULED if schedule_at else PublishJobStatus.QUEUED,
                scheduled_at=schedule_at
            )
            self.db.add(job)
            article.published_target_id = target_id
        
        # Update source stats
        if article.source_id:
            from app.models.source import Source
            source_query = select(Source).where(Source.id == article.source_id)
            source_result = await self.db.execute(source_query)
            source = source_result.scalar_one_or_none()
            if source:
                source.approved_articles += 1
        
        await self.db.commit()
        
        # Audit log
        await self.audit.log(
            action=AuditAction.ARTICLE_APPROVED,
            entity_type="article",
            entity_id=article.id,
            actor_id=user_id,
            actor_type="user",
            before_state=before_state,
            after_state={
                "status": article.status.value,
                "scheduled_at": str(schedule_at) if schedule_at else None,
                "target_id": str(target_id) if target_id else None
            }
        )
        
        # Queue publish job if not scheduled
        if not schedule_at and target_id:
            from app.workers.tasks import execute_publish_job_task
            execute_publish_job_task.delay(str(job.id))
        
        logger.info(
            "Article approved",
            article_id=str(article_id),
            user_id=str(user_id),
            scheduled=bool(schedule_at)
        )
        
        message = "Статья запланирована" if schedule_at else "Статья одобрена и отправлена на публикацию"
        return {"success": True, "message": message, "job_id": str(job.id) if target_id else None}
    
    async def reject_article(
        self,
        article_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject article"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "message": "Article not found"}
        
        if article.status not in [ArticleStatus.PENDING, ArticleStatus.NEEDS_REVIEW]:
            return {"success": False, "message": f"Cannot reject article with status {article.status.value}"}
        
        before_state = {"status": article.status.value}
        
        article.status = ArticleStatus.REJECTED
        article.moderated_at = datetime.utcnow()
        article.moderator_id = user_id
        article.rejection_reason = reason
        
        # Update source stats
        if article.source_id:
            from app.models.source import Source
            source_query = select(Source).where(Source.id == article.source_id)
            source_result = await self.db.execute(source_query)
            source = source_result.scalar_one_or_none()
            if source:
                source.rejected_articles += 1
        
        await self.db.commit()
        
        # Audit log
        await self.audit.log(
            action=AuditAction.ARTICLE_REJECTED,
            entity_type="article",
            entity_id=article.id,
            actor_id=user_id,
            actor_type="user",
            before_state=before_state,
            after_state={"status": article.status.value, "reason": reason}
        )
        
        logger.info(
            "Article rejected",
            article_id=str(article_id),
            user_id=str(user_id),
            reason=reason
        )
        
        return {"success": True, "message": "Статья отклонена"}
    
    async def schedule_article(
        self,
        article_id: UUID,
        user_id: UUID,
        scheduled_at: datetime,
        target_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Schedule article for future publishing"""
        if scheduled_at <= datetime.utcnow():
            return {"success": False, "message": "Scheduled time must be in the future"}
        
        return await self.approve_article(
            article_id=article_id,
            user_id=user_id,
            target_id=target_id,
            schedule_at=scheduled_at
        )
    
    async def publish_now(
        self,
        article_id: UUID,
        user_id: UUID,
        target_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Publish article immediately"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "message": "Article not found"}
        
        if article.status == ArticleStatus.PUBLISHED:
            return {"success": False, "message": "Article already published"}
        
        # If already approved/scheduled, just publish
        if article.status in [ArticleStatus.APPROVED, ArticleStatus.SCHEDULED]:
            # Find existing job or create new one
            job_query = select(PublishJob).where(
                and_(
                    PublishJob.article_id == article_id,
                    PublishJob.status.in_([PublishJobStatus.QUEUED, PublishJobStatus.SCHEDULED])
                )
            )
            job_result = await self.db.execute(job_query)
            job = job_result.scalar_one_or_none()
            
            if job:
                job.status = PublishJobStatus.QUEUED
                job.scheduled_at = None
                await self.db.commit()
                
                from app.workers.tasks import execute_publish_job_task
                execute_publish_job_task.delay(str(job.id))
                
                return {"success": True, "message": "Публикация запущена", "job_id": str(job.id)}
        
        # Otherwise approve and publish
        return await self.approve_article(
            article_id=article_id,
            user_id=user_id,
            target_id=target_id
        )
    
    async def retry_publish(
        self,
        article_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Retry failed publishing"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "message": "Article not found"}
        
        if article.status != ArticleStatus.FAILED:
            return {"success": False, "message": "Can only retry failed articles"}
        
        # Find failed job
        job_query = select(PublishJob).where(
            and_(
                PublishJob.article_id == article_id,
                PublishJob.status == PublishJobStatus.FAILED
            )
        ).order_by(PublishJob.created_at.desc())
        
        job_result = await self.db.execute(job_query)
        job = job_result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "message": "No failed job found"}
        
        # Reset job
        job.status = PublishJobStatus.QUEUED
        job.retries_count = 0
        job.last_error = None
        
        # Reset article
        article.status = ArticleStatus.APPROVED
        
        await self.db.commit()
        
        # Queue job
        from app.workers.tasks import execute_publish_job_task
        execute_publish_job_task.delay(str(job.id))
        
        logger.info("Retry publish", article_id=str(article_id), job_id=str(job.id))
        
        return {"success": True, "message": "Повторная публикация запущена", "job_id": str(job.id)}
    
    async def bulk_approve(
        self,
        article_ids: List[UUID],
        user_id: UUID,
        target_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Bulk approve multiple articles"""
        success_count = 0
        failed_count = 0
        failed_ids = []
        
        for article_id in article_ids:
            result = await self.approve_article(
                article_id=article_id,
                user_id=user_id,
                target_id=target_id
            )
            
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(article_id)
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
            "message": f"Одобрено: {success_count}, ошибок: {failed_count}"
        }
    
    async def bulk_reject(
        self,
        article_ids: List[UUID],
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bulk reject multiple articles"""
        success_count = 0
        failed_count = 0
        failed_ids = []
        
        for article_id in article_ids:
            result = await self.reject_article(
                article_id=article_id,
                user_id=user_id,
                reason=reason
            )
            
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(article_id)
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
            "message": f"Отклонено: {success_count}, ошибок: {failed_count}"
        }
    
    async def approve_batch(
        self,
        batch_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Approve all articles in batch"""
        query = select(Batch).where(Batch.id == batch_id)
        result = await self.db.execute(query)
        batch = result.scalar_one_or_none()
        
        if not batch:
            return {"success": False, "message": "Batch not found"}
        
        # Get batch articles
        articles_query = select(Article).where(
            and_(
                Article.batch_id == batch_id,
                Article.status == ArticleStatus.PENDING
            )
        )
        articles_result = await self.db.execute(articles_query)
        articles = articles_result.scalars().all()
        
        article_ids = [a.id for a in articles]
        result = await self.bulk_approve(article_ids, user_id)
        
        # Update batch status
        batch.status = BatchStatus.COMPLETED
        await self.db.commit()
        
        return {
            "success": True,
            "approved_count": result["success_count"],
            "failed_count": result["failed_count"],
            "message": f"Пакет одобрен: {result['success_count']} статей"
        }
    
    async def reject_batch(
        self,
        batch_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject all articles in batch"""
        query = select(Batch).where(Batch.id == batch_id)
        result = await self.db.execute(query)
        batch = result.scalar_one_or_none()
        
        if not batch:
            return {"success": False, "message": "Batch not found"}
        
        # Get batch articles
        articles_query = select(Article).where(
            and_(
                Article.batch_id == batch_id,
                Article.status == ArticleStatus.PENDING
            )
        )
        articles_result = await self.db.execute(articles_query)
        articles = articles_result.scalars().all()
        
        article_ids = [a.id for a in articles]
        result = await self.bulk_reject(article_ids, user_id, reason)
        
        # Update batch status
        batch.status = BatchStatus.COMPLETED
        await self.db.commit()
        
        return {
            "success": True,
            "rejected_count": result["success_count"],
            "failed_count": result["failed_count"],
            "message": f"Пакет отклонен: {result['success_count']} статей"
        }