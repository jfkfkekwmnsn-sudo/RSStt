from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import openai
from openai import AsyncOpenAI

from app.config import settings
from app.models.article import Article
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction
from app.utils.redis import get_redis
import structlog

logger = structlog.get_logger()


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    # Default prompts
    REWRITE_PROMPT = """Перепиши следующий текст новости для публикации в Telegram-канале.
Требования:
- Сохрани все ключевые факты и смысл
- Сделай текст более читабельным и лаконичным
- Используй нейтральный информационный стиль
- Длина: 2-4 абзаца
- Не добавляй эмодзи и хештеги

Исходный текст:
{text}

Переписанный текст:"""

    SUMMARIZE_PROMPT = """Создай краткое резюме следующей новости в 2-3 предложения.
Выдели только самое важное.

Текст:
{text}

Резюме:"""

    TITLE_PROMPT = """Придумай 3 варианта заголовка для следующей новости.
Заголовки должны быть информативными и привлекательными, но не кликбейтными.

Текст:
{text}

Варианты заголовков (по одному на строку):"""

    CATEGORIZE_PROMPT = """Определи категорию для следующей новости.
Доступные категории: технологии, политика, экономика, спорт, наука, культура, новости

Текст:
{text}

Категория (только одно слово):"""

    async def rewrite_article(
        self,
        article_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Rewrite article using AI"""
        if not settings.AI_ENABLED or not self.client:
            return {"success": False, "message": "AI is disabled"}
        
        # Check rate limits
        if not await self._check_rate_limit():
            return {"success": False, "message": "AI rate limit exceeded"}
        
        # Get article
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "message": "Article not found"}
        
        text = article.content_clean or article.description or article.title
        if not text:
            return {"success": False, "message": "No content to rewrite"}
        
        try:
            # Store original
            original_text = article.content_clean
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты профессиональный редактор новостного Telegram-канала."},
                    {"role": "user", "content": self.REWRITE_PROMPT.format(text=text[:3000])}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            rewritten = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            # Update article
            article.content_clean = rewritten
            article.ai_used = True
            article.ai_metadata = {
                "rewrite": {
                    "original_length": len(original_text) if original_text else 0,
                    "new_length": len(rewritten),
                    "tokens_used": tokens_used,
                    "model": settings.OPENAI_MODEL,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self.db.commit()
            
            # Update token counter
            await self._increment_token_counter(tokens_used)
            
            # Audit
            await self.audit.log(
                action=AuditAction.AI_PROCESSED,
                entity_type="article",
                entity_id=article.id,
                actor_id=user_id,
                actor_type="user" if user_id else "system",
                metadata={"action": "rewrite", "tokens": tokens_used}
            )
            
            logger.info(
                "AI rewrite completed",
                article_id=str(article_id),
                tokens=tokens_used
            )
            
            return {
                "success": True,
                "message": "Article rewritten",
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error("AI rewrite failed", article_id=str(article_id), error=str(e))
            return {"success": False, "message": str(e)}
    
    async def summarize(self, text: str) -> Dict[str, Any]:
        """Summarize text"""
        if not settings.AI_ENABLED or not self.client:
            return {"success": False, "message": "AI is disabled"}
        
        if not await self._check_rate_limit():
            return {"success": False, "message": "AI rate limit exceeded"}
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты помощник для создания кратких резюме новостей."},
                    {"role": "user", "content": self.SUMMARIZE_PROMPT.format(text=text[:3000])}
                ],
                max_tokens=300,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            await self._increment_token_counter(tokens_used)
            
            return {
                "success": True,
                "summary": summary,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error("AI summarize failed", error=str(e))
            return {"success": False, "message": str(e)}
    
    async def generate_titles(self, text: str) -> Dict[str, Any]:
        """Generate title variants"""
        if not settings.AI_ENABLED or not self.client:
            return {"success": False, "message": "AI is disabled"}
        
        if not await self._check_rate_limit():
            return {"success": False, "message": "AI rate limit exceeded"}
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты помощник для создания заголовков новостей."},
                    {"role": "user", "content": self.TITLE_PROMPT.format(text=text[:2000])}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            titles_text = response.choices[0].message.content.strip()
            titles = [t.strip().lstrip("0123456789.-) ") for t in titles_text.split("\n") if t.strip()]
            tokens_used = response.usage.total_tokens
            
            await self._increment_token_counter(tokens_used)
            
            return {
                "success": True,
                "titles": titles[:5],
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error("AI generate titles failed", error=str(e))
            return {"success": False, "message": str(e)}
    
    async def categorize(self, text: str) -> Dict[str, Any]:
        """Categorize text"""
        if not settings.AI_ENABLED or not self.client:
            return {"success": False, "message": "AI is disabled"}
        
        if not await self._check_rate_limit():
            return {"success": False, "message": "AI rate limit exceeded"}
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты помощник для категоризации новостей."},
                    {"role": "user", "content": self.CATEGORIZE_PROMPT.format(text=text[:1500])}
                ],
                max_tokens=20,
                temperature=0.3
            )
            
            category = response.choices[0].message.content.strip().lower()
            tokens_used = response.usage.total_tokens
            
            # Validate category
            valid_categories = ["технологии", "политика", "экономика", "спорт", "наука", "культура", "новости"]
            if category not in valid_categories:
                category = "новости"
            
            await self._increment_token_counter(tokens_used)
            
            return {
                "success": True,
                "category": category,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error("AI categorize failed", error=str(e))
            return {"success": False, "message": str(e)}
    
    async def _check_rate_limit(self) -> bool:
        """Check if within daily token limit"""
        redis = await get_redis()
        today = date.today().isoformat()
        key = f"ai_tokens:{today}"
        
        current = await redis.get(key)
        if current:
            current_tokens = int(current)
            if current_tokens >= settings.AI_MAX_TOKENS_PER_DAY:
                logger.warning("AI rate limit exceeded", tokens=current_tokens)
                return False
        
        return True
    
    async def _increment_token_counter(self, tokens: int):
        """Increment daily token counter"""
        redis = await get_redis()
        today = date.today().isoformat()
        key = f"ai_tokens:{today}"
        
        await redis.incrby(key, tokens)
        await redis.expire(key, 86400 * 2)  # Keep for 2 days
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get AI usage statistics"""
        redis = await get_redis()
        today = date.today().isoformat()
        key = f"ai_tokens:{today}"
        
        current = await redis.get(key)
        tokens_today = int(current) if current else 0
        
        return {
            "tokens_today": tokens_today,
            "limit": settings.AI_MAX_TOKENS_PER_DAY,
            "remaining": max(0, settings.AI_MAX_TOKENS_PER_DAY - tokens_today),
            "usage_percent": (tokens_today / settings.AI_MAX_TOKENS_PER_DAY * 100) if settings.AI_MAX_TOKENS_PER_DAY > 0 else 0
        }