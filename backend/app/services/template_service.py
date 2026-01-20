from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import re

from app.models.template import Template
from app.models.article import Article
from app.models.publish_target import PublishTarget
import structlog

logger = structlog.get_logger()


class TemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Category emojis
    CATEGORY_EMOJI = {
        "технологии": "💻",
        "политика": "🏛",
        "экономика": "📈",
        "спорт": "⚽",
        "наука": "🔬",
        "культура": "🎭",
        "новости": "📰",
    }
    
    # Default template
    DEFAULT_TEMPLATE = """
{emoji} <b>{title}</b>

{text}

🔗 <a href="{url}">Читать полностью</a>

{tags}
""".strip()
    
    async def render_for_article(
        self,
        article_id: UUID,
        template_id: Optional[UUID] = None,
        target_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Render template for article"""
        # Get article
        query = select(Article).where(Article.id == article_id)
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        
        if not article:
            return {"text": "", "warnings": ["Article not found"]}
        
        # Get template
        template = None
        if template_id:
            template = await self._get_template(template_id)
        
        if not template and target_id:
            template = await self._find_template_for_target(target_id, article.category)
        
        if not template:
            template = await self._find_default_template(article.category)
        
        # Render
        return await self._render(article, template)
    
    async def _get_template(self, template_id: UUID) -> Optional[Template]:
        """Get template by ID"""
        query = select(Template).where(
            Template.id == template_id,
            Template.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _find_template_for_target(self, target_id: UUID, category: Optional[str]) -> Optional[Template]:
        """Find best template for target and category"""
        # First try target + category specific
        if category:
            query = select(Template).where(
                and_(
                    Template.is_active == True,
                    Template.scope == "target",
                    Template.scope_value == str(target_id)
                )
            )
            result = await self.db.execute(query)
            template = result.scalar_one_or_none()
            if template:
                return template
        
        # Try category specific
        if category:
            query = select(Template).where(
                and_(
                    Template.is_active == True,
                    Template.scope == "category",
                    Template.scope_value == category
                )
            )
            result = await self.db.execute(query)
            template = result.scalar_one_or_none()
            if template:
                return template
        
        return None
    
    async def _find_default_template(self, category: Optional[str]) -> Optional[Template]:
        """Find default template"""
        # Try global default
        query = select(Template).where(
            and_(
                Template.is_active == True,
                Template.scope == "global",
                Template.is_default == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _render(self, article: Article, template: Optional[Template]) -> Dict[str, Any]:
        """Render template with article data"""
        template_body = template.body if template else self.DEFAULT_TEMPLATE
        auto_hashtags = template.auto_hashtags if template else []
        
        warnings = []
        
        # Prepare variables
        emoji = self.CATEGORY_EMOJI.get(article.category, "📰")
        
        # Prepare text
        text = article.content_clean or article.description or ""
        # Limit text length for Telegram
        max_text_len = 800  # Leave room for other parts
        if len(text) > max_text_len:
            text = text[:max_text_len].rsplit(" ", 1)[0] + "..."
        
        # Prepare tags
        tags = article.tags or []
        if auto_hashtags:
            tags = list(set(tags + auto_hashtags))
        
        # Add AI tag if applicable
        if article.ai_used:
            tags.append("ai")
        
        # Format tags as hashtags
        formatted_tags = " ".join(f"#{tag.replace(' ', '_')}" for tag in tags[:5])
        
        # Variables dict
        variables = {
            "emoji": emoji,
            "title": self._escape_html(article.title),
            "text": self._escape_html(text),
            "url": article.url,
            "date": article.pub_date.strftime("%d.%m.%Y") if article.pub_date else "",
            "tags": formatted_tags,
            "source": "",  # TODO: Add source name
            "category": article.category or "",
        }
        
        # Add source name if available
        if article.source_id:
            from app.models.source import Source
            source_query = select(Source).where(Source.id == article.source_id)
            source_result = await self.db.execute(source_query)
            source = source_result.scalar_one_or_none()
            if source:
                variables["source"] = source.name
        
        # Render template
        rendered = template_body
        for var_name, var_value in variables.items():
            rendered = rendered.replace(f"{{{var_name}}}", str(var_value))
        
        # Clean up empty lines
        rendered = re.sub(r'\n\s*\n\s*\n', '\n\n', rendered)
        rendered = rendered.strip()
        
        # Validate for Telegram
        if len(rendered) > 4096:
            warnings.append("Text too long for Telegram message, will be truncated")
            rendered = rendered[:4000] + "..."
        
        # Check for photo caption limit
        has_image = bool(article.main_image_url)
        if has_image and len(rendered) > 1024:
            warnings.append("Text too long for photo caption (max 1024), will use text message")
        
        return {
            "text": rendered,
            "has_image": has_image,
            "image_url": article.main_image_url,
            "warnings": warnings,
            "length": len(rendered),
            "is_valid_for_telegram": len(rendered) <= 4096
        }
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters for Telegram"""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
    
    async def create_template(self, data: Dict[str, Any]) -> Template:
        """Create new template"""
        template = Template(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def update_template(self, template_id: UUID, data: Dict[str, Any]) -> Optional[Template]:
        """Update template"""
        query = select(Template).where(Template.id == template_id)
        result = await self.db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        for key, value in data.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)
        
        template.version += 1
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def test_render(self, template_id: UUID, article_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Test template rendering"""
        if article_id:
            return await self.render_for_article(article_id, template_id)
        
        # Create dummy article for testing
        dummy_article = Article(
            title="Тестовый заголовок новости",
            content_clean="Это тестовый текст новости для проверки шаблона. Здесь может быть любой контент, который будет отображаться в публикации.",
            category="технологии",
            tags=["тест", "пример"],
            url="https://example.com/news/123",
            main_image_url="https://example.com/image.jpg",
            pub_date=datetime.utcnow()
        )
        
        template = await self._get_template(template_id)
        return await self._render(dummy_article, template)