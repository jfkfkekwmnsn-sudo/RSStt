import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from celery import shared_task
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.database import async_session_maker
from app.models.source import Source
from app.models.article import Article, ArticleStatus
from app.models.batch import Batch, BatchStatus, BatchStrategy
from app.models.publish_job import PublishJob, PublishJobStatus
from app.services.ingestion_service import IngestionService
from app.services.processing_service import ProcessingService
from app.services.publishing_service import PublishingService
from app.services.batch_service import BatchService
from app.config import settings
import structlog

logger = structlog.get_logger()


def run_async(coro):
    """Helper to run async functions in Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_source_task(self, source_id: str):
    """Fetch single source"""
    async def _fetch():
        async with async_session_maker() as db:
            service = IngestionService(db)
            result = await service.fetch_source(UUID(source_id))
            return result
    
    try:
        result = run_async(_fetch())
        logger.info("Source fetched", source_id=source_id, result=result)
        return result
    except Exception as e:
        logger.error("Source fetch failed", source_id=source_id, error=str(e))
        self.retry(exc=e)


@celery_app.task
def fetch_all_sources():
    """Fetch all active sources that are due"""
    async def _fetch_all():
        async with async_session_maker() as db:
            # Get sources that need fetching
            now = datetime.now()
            
            query = select(Source).where(
                Source.is_active == True
            )
            result = await db.execute(query)
            sources = result.scalars().all()
            
            for source in sources:
                # Check if due for fetch
                if source.last_fetch_at:
                    next_fetch = source.last_fetch_at + timedelta(minutes=source.fetch_interval_minutes)
                    if now < next_fetch:
                        continue
                
                # Queue fetch task
                fetch_source_task.delay(str(source.id))
                logger.info("Queued source fetch", source_id=str(source.id), source_name=source.name)
    
    run_async(_fetch_all())
    logger.info("Scheduled source fetches")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_article_task(self, article_id: str):
    """Process single article"""
    async def _process():
        async with async_session_maker() as db:
            service = ProcessingService(db)
            result = await service.process_article(UUID(article_id))
            return result
    
    try:
        result = run_async(_process())
        logger.info("Article processed", article_id=article_id, success=result)
        return result
    except Exception as e:
        logger.error("Article processing failed", article_id=article_id, error=str(e))
        self.retry(exc=e)


@celery_app.task
def create_moderation_batches():
    """Create batches for moderation"""
    async def _create_batches():
        async with async_session_maker() as db:
            service = BatchService(db)
            
            # Get pending articles count
            query = select(func.count(Article.id)).where(
                Article.status == ArticleStatus.PENDING,
                Article.batch_id == None
            )
            result = await db.execute(query)
            pending_count = result.scalar()
            
            if pending_count < 3:  # Minimum batch size
                return {"message": "Not enough articles for batch", "pending": pending_count}
            
            # Create batches
            batches_created = await service.create_batches(
                strategy=BatchStrategy.BY_PRIORITY,
                batch_size=5,
                max_batches=3
            )
            
            return {"batches_created": batches_created}
    
    result = run_async(_create_batches())
    logger.info("Batches created", result=result)
    return result


@celery_app.task
def send_batches_to_telegram():
    """Send pending batches to Telegram for moderation"""
    async def _send_batches():
        async with async_session_maker() as db:
            service = BatchService(db)
            
            # Get unsent batches
            query = select(Batch).where(
                Batch.status == BatchStatus.PENDING
            ).limit(5)
            
            result = await db.execute(query)
            batches = result.scalars().all()
            
            sent_count = 0
            for batch in batches:
                success = await service.send_to_telegram(batch.id)
                if success:
                    sent_count += 1
            
            return {"sent": sent_count}
    
    result = run_async(_send_batches())
    logger.info("Batches sent to Telegram", result=result)
    return result


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def execute_publish_job_task(self, job_id: str):
    """Execute single publish job"""
    async def _execute():
        async with async_session_maker() as db:
            service = PublishingService(db)
            result = await service.execute_publish_job(UUID(job_id))
            return result
    
    try:
        result = run_async(_execute())
        logger.info("Publish job executed", job_id=job_id, result=result)
        return result
    except Exception as e:
        logger.error("Publish job failed", job_id=job_id, error=str(e))
        self.retry(exc=e)


@celery_app.task
def execute_scheduled_jobs():
    """Execute publish jobs that are scheduled for now"""
    async def _execute_scheduled():
        async with async_session_maker() as db:
            now = datetime.now()
            
            # Get due jobs
            query = select(PublishJob).where(
                and_(
                    PublishJob.status == PublishJobStatus.SCHEDULED,
                    PublishJob.scheduled_at <= now
                )
            ).limit(10)
            
            result = await db.execute(query)
            jobs = result.scalars().all()
            
            for job in jobs:
                execute_publish_job_task.delay(str(job.id))
            
            return {"queued": len(jobs)}
    
    result = run_async(_execute_scheduled())
    if result.get("queued", 0) > 0:
        logger.info("Scheduled jobs queued", result=result)
    return result


@celery_app.task
def ai_rewrite_task(article_id: str, user_id: Optional[str] = None):
    """Apply AI rewriting to article"""
    async def _rewrite():
        async with async_session_maker() as db:
            from app.services.ai_service import AIService
            service = AIService(db)
            
            result = await service.rewrite_article(
                UUID(article_id),
                UUID(user_id) if user_id else None
            )
            return result
    
    result = run_async(_rewrite())
    logger.info("AI rewrite completed", article_id=article_id, success=result.get("success"))
    return result


@celery_app.task
def housekeeping():
    """Daily housekeeping tasks"""
    async def _housekeeping():
        async with async_session_maker() as db:
            # Archive old rejected articles (older than 30 days)
            cutoff = datetime.now() - timedelta(days=30)
            
            query = select(Article).where(
                and_(
                    Article.status == ArticleStatus.REJECTED,
                    Article.updated_at < cutoff
                )
            )
            result = await db.execute(query)
            old_articles = result.scalars().all()
            
            # For now, just count them. Could move to archive table.
            archived_count = len(old_articles)
            
            # Clean up old source runs (older than 7 days)
            from app.models.source import SourceRun
            run_cutoff = datetime.now() - timedelta(days=7)
            
            delete_runs = await db.execute(
                select(func.count(SourceRun.id)).where(
                    SourceRun.started_at < run_cutoff
                )
            )
            
            # Clean up expired Redis keys
            from app.utils.redis import get_redis
            redis = await get_redis()
            # Redis handles expiry automatically, but we could do cleanup here
            
            return {
                "archived_articles": archived_count,
                "old_runs_found": delete_runs.scalar()
            }
    
    result = run_async(_housekeeping())
    logger.info("Housekeeping completed", result=result)
    return result


@celery_app.task
def update_source_reputations():
    """Update reputation scores for all sources"""
    async def _update_reputations():
        async with async_session_maker() as db:
            query = select(Source).where(Source.is_active == True)
            result = await db.execute(query)
            sources = result.scalars().all()
            
            updated = 0
            for source in sources:
                total = source.total_articles
                if total == 0:
                    continue
                
                # Calculate reputation based on approval rate
                approval_rate = source.approved_articles / total if total > 0 else 0.5
                
                # Factor in error rate
                error_penalty = min(source.consecutive_errors * 0.1, 0.3)
                
                # New reputation
                new_reputation = max(0.1, min(1.0, approval_rate - error_penalty))
                
                if abs(source.reputation_score - new_reputation) > 0.01:
                    source.reputation_score = new_reputation
                    updated += 1
            
            await db.commit()
            return {"updated": updated}
    
    result = run_async(_update_reputations())
    logger.info("Source reputations updated", result=result)
    return result


@celery_app.task
def send_alert(alert_type: str, message: str, data: Optional[dict] = None):
    """Send alert to Telegram"""
    async def _send_alert():
        from aiogram import Bot
        
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_MODERATION_CHAT_ID:
            return {"success": False, "message": "Telegram not configured"}
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        emoji = {
            "error": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅",
        }.get(alert_type, "📢")
        
        text = f"{emoji} <b>Уведомление</b>\n\n{message}"
        
        if data:
            text += "\n\n<pre>" + str(data) + "</pre>"
        
        try:
            await bot.send_message(
                chat_id=settings.TELEGRAM_MODERATION_CHAT_ID,
                text=text,
                parse_mode="HTML"
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await bot.session.close()
    
    result = run_async(_send_alert())
    return result
