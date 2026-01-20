import hashlib
import re
from typing import Optional
from uuid import UUID
import structlog

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.models.source import Source
from app.config import settings

logger = structlog.get_logger()


class ProcessingService:
    """Service for processing and enriching articles"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_article(self, article_id: UUID) -> dict:
        """Process a single article"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"success": False, "error": "Article not found"}
        
        try:
            # Step 1: Clean content
            await self._clean_content(article)
            
            # Step 2: Calculate quality score
            await self._calculate_quality(article)
            
            # Step 3: Calculate priority
            await self._calculate_priority(article)
            
            # Step 4: Extract images
            await self._extract_images(article)
            
            # Step 5: Check for duplicates
            await self._check_duplicates(article)
            
            article.status = ArticleStatus.PENDING
            
            await self.db.commit()
            
            logger.info("Article processed", article_id=str(article_id))
            return {"success": True, "quality_score": article.quality_score}
            
        except Exception as e:
            article.status = ArticleStatus.FAILED
            await self.db.commit()
            logger.error("Article processing failed", article_id=str(article_id), error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _clean_content(self, article: Article):
        """Clean article content"""
        if not article.content_raw:
            return
        
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', article.content_raw)
        content = re.sub(r'[ \t]{2,}', ' ', content)
        
        # Remove common tracking elements
        content = re.sub(r'utm_source=[^&\s]*', '', content)
        content = re.sub(r'utm_medium=[^&\s]*', '', content)
        content = re.sub(r'utm_campaign=[^&\s]*', '', content)
        
        # Basic HTML cleanup (in production, use BeautifulSoup)
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        
        article.content_clean = content.strip()
    
    async def _calculate_quality(self, article: Article):
        """Calculate article quality score"""
        factors = {}
        score = 0.5  # Base score
        
        # Length factor
        if article.content_clean:
            word_count = len(article.content_clean.split())
            if 200 <= word_count <= 5000:
                score += 0.2
                factors["length_ok"] = True
            elif word_count < 200:
                score -= 0.1
                factors["too_short"] = word_count
            else:
                factors["too_long"] = word_count
        
        # Title quality
        if article.title:
            title_length = len(article.title)
            if 30 <= title_length <= 150:
                score += 0.1
                factors["title_ok"] = True
            elif title_length < 30:
                factors["short_title"] = title_length
            else:
                factors["long_title"] = title_length
        
        # Has description
        if article.description:
            score += 0.1
            factors["has_description"] = True
        
        # Has images
        if article.main_image_url:
            score += 0.1
            factors["has_image"] = True
        
        # Source reputation factor
        if article.source_id:
            query = select(Source).where(Source.id == article.source_id)
            result = await self.db.execute(query)
            source = result.scalar_one_or_none()
            if source:
                score = score * source.reputation_score
                factors["source_reputation"] = source.reputation_score
        
        # Clamp score
        article.quality_score = max(0.0, min(1.0, score))
        article.quality_factors = factors
    
    async def _calculate_priority(self, article: Article):
        """Calculate article priority score"""
        priority = 50  # Base priority
        factors = {}
        
        # Quality factor
        priority += int(article.quality_score * 30)
        factors["quality"] = article.quality_score
        
        # Recency factor
        if article.pub_date:
            hours_old = (article.pub_date - article.pub_date).total_seconds() / 3600
            if hours_old < 1:
                priority += 20
                factors["recency"] = "fresh"
            elif hours_old < 6:
                priority += 10
                factors["recency"] = "recent"
            elif hours_old > 48:
                priority -= 10
                factors["recency"] = "old"
        
        # Source factor
        if article.source_id:
            query = select(Source).where(Source.id == article.source_id)
            result = await self.db.execute(query)
            source = result.scalar_one_or_none()
            if source:
                priority += int((source.reputation_score - 0.5) * 20)
                factors["source_score"] = source.reputation_score
        
        article.priority_score = max(0, min(100, priority))
        article.priority_factors = factors
    
    async def _extract_images(self, article: Article):
        """Extract main image from article"""
        if not article.content_clean:
            return
        
        # Simple image extraction - in production use proper HTML parsing
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', article.content_clean)
        if img_match:
            article.main_image_url = img_match.group(1)
            
            # Store images info
            article.images = {
                "main": article.main_image_url,
                "count": len(re.findall(r'<img[^>]+>', article.content_clean))
            }
    
    async def _check_duplicates(self, article: Article):
        """Check for duplicate articles based on content hash"""
        if not article.content_clean:
            return
        
        content_hash = hashlib.md5(article.content_clean.encode()).hexdigest()
        article.content_hash = content_hash
        
        # Check for similar content
        query = select(Article).where(
            and_(
                Article.id != article.id,
                Article.content_hash == content_hash,
                Article.status != ArticleStatus.REJECTED
            )
        )
        result = await self.db.execute(query)
        duplicate = result.scalar_one_or_none()
        
        if duplicate:
            article.status = ArticleStatus.DUPLICATE
            article.similar_to_id = duplicate.id
            article.similarity_score = 1.0
    
    async def bulk_process(self, limit: int = 100) -> dict:
        """Process multiple unprocessed articles"""
        query = select(Article).where(
            and_(
                Article.status == ArticleStatus.PENDING,
                Article.content_clean == None
            )
        ).limit(limit)
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        processed = 0
        failed = 0
        
        for article in articles:
            result = await self.process_article(article.id)
            if result["success"]:
                processed += 1
            else:
                failed += 1
        
        return {"processed": processed, "failed": failed}