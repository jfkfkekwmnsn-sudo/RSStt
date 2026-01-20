import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import feedparser
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.config import settings
from app.models.source import Source, SourceRun, SourceType
from app.models.article import Article, ArticleStatus
from app.services.processing_service import ProcessingService
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction
from app.utils.url import normalize_url, hash_url
import structlog

logger = structlog.get_logger()


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.processing = ProcessingService(db)
        self.audit = AuditService(db)
    
    async def fetch_source(self, source_id: UUID) -> Dict[str, Any]:
        """Fetch articles from a source"""
        query = select(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        source = result.scalar_one_or_none()
        
        if not source:
            return {"success": False, "message": "Source not found"}
        
        if not source.is_active:
            return {"success": False, "message": "Source is inactive"}
        
        # Create run record
        run = SourceRun(
            source_id=source.id,
            started_at=datetime.utcnow(),
            status="running"
        )
        self.db.add(run)
        await self.db.commit()
        
        try:
            if source.type == SourceType.RSS:
                articles = await self._fetch_rss(source)
            elif source.type == SourceType.SCRAPER:
                articles = await self._fetch_scraper(source)
            else:
                articles = []
            
            # Process articles
            new_count = 0
            dup_count = 0
            
            for article_data in articles:
                is_new = await self._process_article(source, article_data)
                if is_new:
                    new_count += 1
                else:
                    dup_count += 1
            
            # Update run
            run.finished_at = datetime.utcnow()
            run.status = "success"
            run.articles_found = len(articles)
            run.articles_new = new_count
            run.articles_duplicate = dup_count
            
            # Update source
            source.last_fetch_at = datetime.utcnow()
            source.last_error = None
            source.consecutive_errors = 0
            source.total_articles += new_count
            
            await self.db.commit()
            
            logger.info(
                "Source fetched successfully",
                source_id=str(source_id),
                source_name=source.name,
                articles_found=len(articles),
                articles_new=new_count
            )
            
            return {
                "success": True,
                "message": f"Fetched {len(articles)} articles, {new_count} new",
                "run_id": run.id
            }
            
        except Exception as e:
            run.finished_at = datetime.utcnow()
            run.status = "failed"
            run.error_message = str(e)
            
            source.last_error = str(e)
            source.consecutive_errors += 1
            
            await self.db.commit()
            
            logger.error(
                "Source fetch failed",
                source_id=str(source_id),
                error=str(e)
            )
            
            return {"success": False, "message": str(e)}
    
    async def _fetch_rss(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feed"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(source.feed_url)
            response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        articles = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=settings.ARTICLE_FRESHNESS_DAYS)
        
        for entry in feed.entries[:source.max_items_per_fetch]:
            # Parse date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            # Skip old articles
            if pub_date and pub_date < cutoff_date:
                continue
            
            # Normalize URL
            url = normalize_url(entry.link, source.normalization_rules)
            
            articles.append({
                "url": url,
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "content_raw": entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
                "pub_date": pub_date,
            })
        
        return articles
    
    async def _fetch_scraper(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch articles using web scraper"""
        if not source.scraper_config:
            return []
        
        config = source.scraper_config
        articles = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(source.feed_url)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # TODO: Implement scraper logic based on config
        # This is a placeholder for custom scraper implementation
        
        return articles
    
    async def _process_article(self, source: Source, article_data: Dict[str, Any]) -> bool:
        """Process single article, returns True if new"""
        url = article_data["url"]
        url_hash = hash_url(url)
        
        # Check for URL duplicate
        query = select(Article).where(Article.url_hash == url_hash)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            return False
        
        # Create article
        article = Article(
            source_id=source.id,
            url=url,
            url_hash=url_hash,
            title=article_data["title"],
            description=article_data.get("description"),
            content_raw=article_data.get("content_raw"),
            pub_date=article_data.get("pub_date"),
            status=ArticleStatus.PENDING,
        )
        
        self.db.add(article)
        await self.db.commit()
        
        # Queue for processing
        from app.workers.tasks import process_article_task
        process_article_task.delay(str(article.id))
        
        return True
    
    async def process_external_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process article from external webhook"""
        url = data.get("url")
        if not url:
            return {"success": False, "message": "URL is required"}
        
        url_hash = hash_url(normalize_url(url, {}))
        
        # Check duplicate
        query = select(Article).where(Article.url_hash == url_hash)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            return {"success": False, "message": "Article already exists"}
        
        article = Article(
            url=url,
            url_hash=url_hash,
            title=data.get("title", "Untitled"),
            description=data.get("description"),
            content_raw=data.get("content"),
            pub_date=data.get("pub_date"),
            status=ArticleStatus.PENDING,
        )
        
        self.db.add(article)
        await self.db.commit()
        
        # Queue for processing
        from app.workers.tasks import process_article_task
        process_article_task.delay(str(article.id))
        
        return {
            "success": True,
            "message": "Article queued for processing",
            "article_id": str(article.id)
        }