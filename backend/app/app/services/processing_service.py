import hashlib
import re
from typing import Optional, List, Dict, Any
from uuid import UUID
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.config import settings
from app.models.article import Article, ArticleStatus
from app.models.source import Source
from app.services.rules_service import RulesService
import structlog

logger = structlog.get_logger()


class ProcessingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules_service = RulesService(db)
    
    async def process_article(self, article_id: UUID) -> bool:
        """Full processing pipeline for article"""
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return False
        
        try:
            # 1. Clean content
            await self._clean_content(article)
            
            # 2. Check content duplicate
            if await self._check_content_duplicate(article):
                article.status = ArticleStatus.DUPLICATE
                await self.db.commit()
                return True
            
            # 3. Extract images
            await self._extract_images(article)
            
            # 4. Categorize
            await self._categorize(article)
            
            # 5. Calculate quality score
            await self._calculate_quality(article)
            
            # 6. Calculate priority
            await self._calculate_priority(article)
            
            # 7. Apply rules
            await self.rules_service.apply_rules(article)
            
            await self.db.commit()
            
            logger.info(
                "Article processed",
                article_id=str(article_id),
                quality=article.quality_score,
                priority=article.priority_score,
                status=article.status.value
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Article processing failed",
                article_id=str(article_id),
                error=str(e)
            )
            return False
    
    async def _clean_content(self, article: Article):
        """Clean and normalize content"""
        content = article.content_raw or article.description or ""
        
        if content:
            # Parse HTML
            soup = BeautifulSoup(content, 'lxml')
            
            # Remove scripts, styles, etc.
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Normalize whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            article.content_clean = text.strip()
            
            # Calculate content hash
            article.content_hash = hashlib.sha256(
                article.content_clean.encode()
            ).hexdigest()
    
    async def _check_content_duplicate(self, article: Article) -> bool:
        """Check if content is duplicate"""
        if not article.content_hash:
            return False
        
        query = select(Article).where(
            and_(
                Article.content_hash == article.content_hash,
                Article.id != article.id
            )
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            article.similar_to_id = existing.id
            article.similarity_score = 1.0
            return True
        
        return False
    
    async def _extract_images(self, article: Article):
        """Extract images from content"""
        content = article.content_raw or ""
        
        if not content:
            return
        
        soup = BeautifulSoup(content, 'lxml')
        images = []
        
        for img in soup.find_all('img', src=True)[:5]:  # Limit to 5 images
            src = img.get('src', '')
            if src and src.startswith(('http://', 'https://')):
                images.append({
                    "url": src,
                    "alt": img.get('alt', ''),
                    "is_main": len(images) == 0
                })
        
        if images:
            article.images = images
            article.main_image_url = images[0]["url"]
    
    async def _categorize(self, article: Article):
        """Categorize article by keywords"""
        # Simple keyword-based categorization
        categories = {
            "технологии": ["технолог", "it", "компьютер", "программ", "искусственный интеллект", "ai", "software"],
            "политика": ["политик", "правительств", "президент", "выбор", "закон", "депутат"],
            "экономика": ["экономик", "финанс", "банк", "рубль", "доллар", "акци", "биржа"],
            "спорт": ["спорт", "футбол", "хоккей", "олимпи", "чемпионат", "матч"],
            "наука": ["наука", "ученые", "исследован", "открыти", "эксперимент"],
            "культура": ["культур", "кино", "музык", "театр", "выставк", "концерт"],
        }
        
        text = f"{article.title} {article.content_clean or ''}".lower()
        
        best_category = "новости"  # default
        best_score = 0
        
        for category, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_category = category
        
        article.category = best_category
    
    async def _calculate_quality(self, article: Article):
        """Calculate quality score (0-1)"""
        factors = {}
        
        # Has image (0.2)
        has_image = bool(article.main_image_url)
        factors["has_image"] = 0.2 if has_image else 0.0
        
        # Text length (0.3)
        text_len = len(article.content_clean or "")
        if text_len > 2000:
            factors["text_length"] = 0.3
        elif text_len > 1000:
            factors["text_length"] = 0.2
        elif text_len > 500:
            factors["text_length"] = 0.15
        else:
            factors["text_length"] = 0.05
        
        # Freshness (0.2)
        if article.pub_date:
            from datetime import datetime, timedelta
            age_hours = (datetime.utcnow() - article.pub_date).total_seconds() / 3600
            if age_hours < 6:
                factors["freshness"] = 0.2
            elif age_hours < 24:
                factors["freshness"] = 0.15
            elif age_hours < 72:
                factors["freshness"] = 0.1
            else:
                factors["freshness"] = 0.05
        else:
            factors["freshness"] = 0.1
        
        # Source trust (0.2)
        if article.source_id:
            query = select(Source).where(Source.id == article.source_id)
            result = await self.db.execute(query)
            source = result.scalar_one_or_none()
            if source:
                if source.is_trusted:
                    factors["source_trust"] = 0.2
                else:
                    factors["source_trust"] = source.reputation_score * 0.2
            else:
                factors["source_trust"] = 0.1
        else:
            factors["source_trust"] = 0.1
        
        # Uniqueness (0.1) - not duplicate
        factors["uniqueness"] = 0.1 if not article.similar_to_id else 0.0
        
        article.quality_score = sum(factors.values())
        article.quality_factors = factors
    
    async def _calculate_priority(self, article: Article):
        """Calculate priority score (0-100)"""
        factors = {}
        
        # Base priority
        priority = 50
        
        # Category weight
        category_weights = {
            "политика": 20,
            "экономика": 15,
            "технологии": 10,
            "наука": 10,
            "спорт": 5,
            "культура": 5,
            "новости": 0,
        }
        category_bonus = category_weights.get(article.category, 0)
        factors["category_weight"] = category_bonus
        priority += category_bonus
        
        # Quality bonus
        quality_bonus = int(article.quality_score * 20)
        factors["quality_bonus"] = quality_bonus
        priority += quality_bonus
        
        # Freshness bonus
        if article.pub_date:
            from datetime import datetime
            age_hours = (datetime.utcnow() - article.pub_date).total_seconds() / 3600
            if age_hours < 3:
                freshness_bonus = 15
            elif age_hours < 12:
                freshness_bonus = 10
            elif age_hours < 24:
                freshness_bonus = 5
            else:
                freshness_bonus = 0
            factors["freshness_bonus"] = freshness_bonus
            priority += freshness_bonus
        
        # Media bonus
        if article.main_image_url:
            factors["media_bonus"] = 5
            priority += 5
        
        # Source bonus (trusted sources)
        if article.source_id:
            query = select(Source).where(Source.id == article.source_id)
            result = await self.db.execute(query)
            source = result.scalar_one_or_none()
            if source and source.is_trusted:
                factors["source_bonus"] = 10
                priority += 10
        
        article.priority_score = min(100, max(0, priority))
        article.priority_factors = factors