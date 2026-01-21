import hashlib
import feedparser
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import structlog

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source, SourceRun, SourceType
from app.models.article import Article, ArticleStatus
from app.config import settings

logger = structlog.get_logger()


class IngestionService:
    """Service for ingesting articles from various sources"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def fetch_source(self, source_id: UUID) -> dict:
        """Fetch articles from a single source"""
        query = select(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        source = result.scalar_one_or_none()
        
        if not source:
            return {"success": False, "error": "Source not found"}
        
        if not source.is_active:
            return {"success": False, "error": "Source is inactive"}
        
        # Create run record
        run = SourceRun(
            source_id=source.id,
            started_at=datetime.now(),
            status="running"
        )
        self.db.add(run)
        
        try:
            if source.type == SourceType.RSS:
                result_data = await self._fetch_rss(source, run)
            elif source.type == SourceType.SCRAPER:
                result_data = await self._fetch_scraper(source, run)
            else:
                result_data = {"success": False, "error": f"Unsupported source type: {source.type}"}
            
            run.finished_at = datetime.now()
            run.status = result_data.get("status", "failed")
            run.articles_found = result_data.get("articles_found", 0)
            run.articles_new = result_data.get("articles_new", 0)
            run.articles_duplicate = result_data.get("articles_duplicate", 0)
            
            if result_data.get("error"):
                run.error_message = result_data["error"]
            
            await self.db.commit()
            return result_data
            
        except Exception as e:
            run.finished_at = datetime.now()
            run.status = "failed"
            run.error_message = str(e)
            await self.db.commit()
            
            # Update source error count
            source.consecutive_errors += 1
            source.last_error = str(e)
            await self.db.commit()
            
            logger.error("Source fetch failed", source_id=source_id, error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _fetch_rss(self, source: Source, run: SourceRun) -> dict:
        """Fetch articles from RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.feed_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        return {"status": "failed", "error": f"HTTP {response.status}"}
                    
                    content = await response.text()
                    
                    # Parse RSS/Atom feed
                    feed = feedparser.parse(content)
                    
                    if feed.bozo:
                        return {"status": "failed", "error": "Failed to parse feed"}
                    
                    articles_found = 0
                    articles_new = 0
                    articles_duplicate = 0
                    
                    for entry in feed.entries[:source.max_items_per_fetch]:
                        articles_found += 1
                        
                        # Extract article data
                        url = entry.get("link", "")
                        if not url:
                            continue
                        
                        url_hash = hashlib.md5(url.encode()).hexdigest()
                        
                        # Check for duplicate
                        dup_query = select(Article).where(Article.url_hash == url_hash)
                        dup_result = await self.db.execute(dup_query)
                        if dup_result.scalar_one_or_none():
                            articles_duplicate += 1
                            continue
                        
                        # Parse publication date
                        pub_date = None
                        if hasattr(entry, "published_parsed"):
                            try:
                                pub_date = datetime(*entry.published_parsed[:6])
                            except:
                                pass
                        elif hasattr(entry, "updated_parsed"):
                            try:
                                pub_date = datetime(*entry.updated_parsed[:6])
                            except:
                                pass
                        
                        # Create article
                        article = Article(
                            source_id=source.id,
                            url=url,
                            url_hash=url_hash,
                            title=entry.get("title", "")[:500],
                            description=entry.get("summary", "")[:2000] if entry.get("summary") else None,
                            content_raw=entry.get("content", [{"value": ""}])[0].get("value", "") if hasattr(entry, "content") else None,
                            pub_date=pub_date,
                            category=self._extract_category(entry),
                            status=ArticleStatus.PENDING,
                        )
                        
                        self.db.add(article)
                        articles_new += 1
                    
                    # Update source stats
                    source.total_articles += articles_new
                    source.last_fetch_at = datetime.now()
                    source.consecutive_errors = 0
                    source.last_error = None
                    
                    await self.db.commit()
                    
                    return {
                        "status": "success",
                        "articles_found": articles_found,
                        "articles_new": articles_new,
                        "articles_duplicate": articles_duplicate
                    }
                    
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _fetch_scraper(self, source: Source, run: SourceRun) -> dict:
        """Fetch articles using custom scraper"""
        # Placeholder for scraper implementation
        # In production, this would use the scraper_config to extract content
        return {
            "status": "success",
            "articles_found": 0,
            "articles_new": 0,
            "articles_duplicate": 0
        }
    
    def _extract_category(self, entry) -> Optional[str]:
        """Extract category from feed entry"""
        # Try different fields for category
        if hasattr(entry, "tags"):
            if entry.tags:
                return entry.tags[0].term
        
        # Check for category in other places
        if hasattr(entry, "category"):
            return entry.category
        
        return None
    
    async def check_source_health(self, source_id: UUID) -> dict:
        """Check if a source is responsive"""
        query = select(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        source = result.scalar_one_or_none()
        
        if not source:
            return {"healthy": False, "error": "Source not found"}
        
        try:
            if source.type == SourceType.RSS:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source.feed_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        return {
                            "healthy": response.status == 200,
                            "status_code": response.status
                        }
            else:
                return {"healthy": True, "status": "unknown"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
