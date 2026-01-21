from typing import Optional
from uuid import UUID
from datetime import datetime
import structlog

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.config import settings

logger = structlog.get_logger()


class AIService:
    """Service for AI-powered article processing"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def rewrite_article(
        self, 
        article_id: UUID, 
        user_id: Optional[UUID] = None
    ) -> dict:
        """Apply AI rewriting to an article"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "error": "Article not found"}
        
        try:
            # Check if AI is configured
            if not settings.OPENAI_API_KEY:
                return {"success": False, "error": "AI not configured"}
            
            # Apply AI rewriting
            rewritten = await self._rewrite_with_ai(article)
            
            if rewritten:
                # Update article directly (version tracking should be in article_service)
                article.content_clean = rewritten
                article.ai_used = True
                article.ai_metadata = {
                    "rewritten_at": datetime.now().isoformat(),
                    "model": settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else "gpt-4"
                }
                
                await self.db.commit()
                
                return {"success": True, "rewritten": True}
            
            return {"success": False, "error": "AI rewriting failed"}
            
        except Exception as e:
            logger.error("AI rewrite failed", article_id=str(article_id), error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _rewrite_with_ai(self, article: Article) -> Optional[str]:
        """Perform actual AI rewriting"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional editor. Rewrite the given article to:
1. Improve clarity and flow
2. Fix grammar and spelling
3. Make it more engaging
4. Keep the original meaning
5. Return only the rewritten content, no explanations"""
                    },
                    {
                        "role": "user",
                        "content": f"Title: {article.title}\n\nContent:\n{article.content_raw or article.content_clean}"
                    }
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            return response.choices[0].message.content if response.choices else None
        except Exception as e:
            logger.error("AI rewrite error", error=str(e))
            return None
    async def summarize_article(self, article_id: UUID) -> dict:
        """Generate a summary of an article"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "error": "Article not found"}
        
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following article in 2-3 sentences."
                    },
                    {
                        "role": "user",
                        "content": f"Title: {article.title}\n\n{article.content_clean or article.content_raw}"
                    }
                ],
                max_tokens=200
            )
            
            summary = response.choices[0].message.content
            
            return {"success": True, "summary": summary}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def suggest_tags(self, article_id: UUID) -> dict:
        """Suggest tags for an article"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "error": "Article not found"}
        
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Suggest 3-5 relevant tags/categories for this article. Return only the tags separated by commas."
                    },
                    {
                        "role": "user",
                        "content": f"Title: {article.title}\n\nContent: {article.content_clean or article.content_raw[:1000]}"
                    }
                ],
                max_tokens=100
            )
            
            tags = [t.strip() for t in response.choices[0].message.content.split(",")]
            
            return {"success": True, "tags": tags}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
