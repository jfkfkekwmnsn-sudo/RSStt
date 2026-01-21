from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from aiogram import Bot

from app.config import settings
from app.models.article import Article, ArticleStatus
from app.models.batch import Batch, BatchStatus, BatchStrategy
from app.telegram.keyboards import ModerationKeyboard
from app.telegram.messages import MessageBuilder
import structlog

logger = structlog.get_logger()


class BatchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
    
    async def create_batches(
        self,
        strategy: BatchStrategy = BatchStrategy.MIXED,
        batch_size: int = 5,
        max_batches: int = 3
    ) -> int:
        """Create batches from pending articles"""
        # Get unbatched pending articles
        query = select(Article).where(
            and_(
                Article.status == ArticleStatus.PENDING,
                Article.batch_id == None
            )
        ).order_by(Article.priority_score.desc())
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        if len(articles) < batch_size:
            return 0
        
        batches_created = 0
        
        for i in range(0, min(len(articles), max_batches * batch_size), batch_size):
            batch_articles = articles[i:i + batch_size]
            
            if len(batch_articles) < batch_size:
                break
            
            # Create batch
            batch = Batch(
                strategy=strategy,
                status=BatchStatus.PENDING,
                articles_count=len(batch_articles),
                avg_quality=sum(a.quality_score for a in batch_articles) / len(batch_articles),
                total_priority=sum(a.priority_score for a in batch_articles)
            )
            self.db.add(batch)
            await self.db.flush()
            
            # Assign articles to batch
            for article in batch_articles:
                article.batch_id = batch.id
            
            batches_created += 1
            
            if batches_created >= max_batches:
                break
        
        await self.db.commit()
        return batches_created
    
    async def send_to_telegram(self, batch_id: UUID) -> bool:
        """Send batch to Telegram for moderation"""
        if not self.bot:
            return False
        
        query = select(Batch).where(Batch.id == batch_id)
        result = await self.db.execute(query)
        batch = result.scalar_one_or_none()
        
        if not batch:
            return False
        
        # Get batch articles
        articles_query = select(Article).where(
            Article.batch_id == batch_id
        ).order_by(Article.priority_score.desc())
        
        articles_result = await self.db.execute(articles_query)
        articles = articles_result.scalars().all()
        
        if not articles:
            return False
        
        try:
            # Build message
            message_text = MessageBuilder.batch_message(articles, str(batch.id))
            keyboard = ModerationKeyboard.batch_actions(str(batch.id))
            
            # Send to moderation chat
            message = await self.bot.send_message(
                chat_id=settings.TELEGRAM_MODERATION_CHAT_ID,
                text=message_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            # Also send individual articles
            article_message_ids = []
            for article in articles:
                article_msg = await self.bot.send_message(
                    chat_id=settings.TELEGRAM_MODERATION_CHAT_ID,
                    text=MessageBuilder.article_card(article),
                    parse_mode="HTML",
                    reply_markup=ModerationKeyboard.article_actions(article.token)
                )
                article_message_ids.append(article_msg.message_id)
            
            # Update batch
            batch.status = BatchStatus.SENT
            batch.telegram_message_ids = {
                "batch_message": message.message_id,
                "article_messages": article_message_ids
            }
            
            await self.db.commit()
            
            logger.info("Batch sent to Telegram", batch_id=str(batch_id), articles=len(articles))
            return True
            
        except Exception as e:
            logger.error("Failed to send batch to Telegram", batch_id=str(batch_id), error=str(e))
            return False
    
    async def get_batch(self, batch_id: UUID) -> Optional[Batch]:
        """Get batch by ID"""
        query = select(Batch).where(Batch.id == batch_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_batch_articles(self, batch_id: UUID) -> List[Article]:
        """Get articles in batch"""
        query = select(Article).where(
            Article.batch_id == batch_id
        ).order_by(Article.priority_score.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
