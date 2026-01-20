from datetime import datetime
from typing import Optional
from uuid import UUID
import structlog

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.models.publish_job import PublishJob, PublishJobStatus
from app.models.publish_target import PublishTarget
from app.config import settings

logger = structlog.get_logger()


class PublishingService:
    """Service for publishing articles to various targets"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute_publish_job(self, job_id: UUID) -> dict:
        """Execute a single publish job"""
        query = select(PublishJob).where(PublishJob.id == job_id)
        result = await self.db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "error": "Job not found"}
        
        try:
            # Get article and target
            article_query = select(Article).where(Article.id == job.article_id)
            article_result = await self.db.execute(article_query)
            article = article_result.scalar_one_or_none()
            
            target_query = select(PublishTarget).where(PublishTarget.id == job.target_id)
            target_result = await self.db.execute(target_query)
            target = target_result.scalar_one_or_none()
            
            if not article or not target:
                return {"success": False, "error": "Article or target not found"}
            
            # Execute publish based on target type
            if target.type == "telegram":
                result = await self._publish_to_telegram(article, target)
            elif target.type == "telegram_channel":
                result = await self._publish_to_telegram_channel(article, target)
            elif target.type == "webhook":
                result = await self._publish_to_webhook(article, target)
            else:
                return {"success": False, "error": f"Unknown target type: {target.type}"}
            
            if result["success"]:
                job.status = PublishJobStatus.PUBLISHED
                job.published_at = datetime.utcnow()
                job.external_post_id = result.get("post_id")
                job.published_content = result.get("content")
                
                article.status = ArticleStatus.PUBLISHED
                article.published_at = datetime.utcnow()
                article.published_target_id = target.id
                article.published_external_id = result.get("post_id")
                article.published_snapshot = result.get("content")
            else:
                job.status = PublishJobStatus.FAILED
                job.last_error = result.get("error")
                job.retries_count += 1
                
                article.status = ArticleStatus.FAILED
            
            await self.db.commit()
            return result
            
        except Exception as e:
            job.status = PublishJobStatus.FAILED
            job.last_error = str(e)
            job.retries_count += 1
            await self.db.commit()
            
            logger.error("Publish job failed", job_id=str(job_id), error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _publish_to_telegram(self, article: Article, target: PublishTarget) -> dict:
        """Publish article to Telegram chat"""
        try:
            from aiogram import Bot
            
            bot = Bot(token=target.config.get("token"))
            
            # Format content for Telegram
            content = self._format_for_telegram(article)
            
            # Send message
            message = await bot.send_message(
                chat_id=target.config.get("chat_id"),
                text=content["text"],
                parse_mode="HTML",
                disable_web_page_preview=content.get("disable_preview", False)
            )
            
            await bot.session.close()
            
            return {
                "success": True,
                "post_id": str(message.message_id),
                "content": {
                    "text": content["text"],
                    "message_id": message.message_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error("Telegram publish failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _publish_to_telegram_channel(self, article: Article, target: PublishTarget) -> dict:
        """Publish article to Telegram channel"""
        # Similar to _publish_to_telegram but with channel-specific logic
        return await self._publish_to_telegram(article, target)
    
    async def _publish_to_webhook(self, article: Article, target: PublishTarget) -> dict:
        """Publish article via webhook"""
        try:
            import aiohttp
            
            payload = {
                "article_id": str(article.id),
                "title": article.title,
                "content": article.content_clean,
                "url": article.url,
                "published_at": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    target.config.get("url"),
                    json=payload,
                    headers=target.config.get("headers", {}),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in (200, 201, 204):
                        return {"success": True, "post_id": None}
                    else:
                        text = await response.text()
                        return {
                            "success": False, 
                            "error": f"Webhook returned {response.status}: {text}"
                        }
                        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_for_telegram(self, article: Article) -> dict:
        """Format article content for Telegram"""
        text = f"<b>{article.title}</b>\n\n"
        
        if article.description:
            # Truncate description if needed
            desc = article.description
            if len(desc) > 500:
                desc = desc[:497] + "..."
            text += f"{desc}\n\n"
        
        text += f"<a href=\"{article.url}\">Читать полностью</a>"
        
        # Telegram message limit is 4096 characters
        if len(text) > 4000:
            text = text[:3997] + "...</b>"
        
        return {
            "text": text,
            "disable_preview": False
        }
    
    async def schedule_publish(
        self, 
        article_id: UUID, 
        target_id: UUID, 
        scheduled_at: Optional[datetime] = None
    ) -> PublishJob:
        """Schedule an article for publishing"""
        job = PublishJob(
            article_id=article_id,
            target_id=target_id,
            scheduled_at=scheduled_at,
            status=PublishJobStatus.SCHEDULED if scheduled_at else PublishJobStatus.QUEUED
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        return job
    
    async def cancel_job(self, job_id: UUID) -> dict:
        """Cancel a scheduled publish job"""
        query = select(PublishJob).where(PublishJob.id == job_id)
        result = await self.db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "error": "Job not found"}
        
        if job.status not in [PublishJobStatus.QUEUED, PublishJobStatus.SCHEDULED]:
            return {"success": False, "error": f"Cannot cancel job in status: {job.status}"}
        
        job.status = PublishJobStatus.CANCELLED
        await self.db.commit()
        
        return {"success": True}