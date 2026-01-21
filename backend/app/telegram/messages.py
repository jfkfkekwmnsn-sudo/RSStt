from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.article import Article, ArticleStatus


class MessageBuilder:
    """Builder for Telegram messages"""
    
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
    
    # Status emojis
    STATUS_EMOJI = {
        ArticleStatus.PENDING: "⏳",
        ArticleStatus.APPROVED: "✅",
        ArticleStatus.REJECTED: "❌",
        ArticleStatus.PUBLISHED: "📤",
        ArticleStatus.SCHEDULED: "⏰",
        ArticleStatus.FAILED: "⚠️",
        ArticleStatus.DUPLICATE: "🔄",
    }
    
    @classmethod
    def article_card(
        cls,
        article: Article,
        include_content: bool = False,
        include_scores: bool = True
    ) -> str:
        """Build article card message"""
        emoji = cls.CATEGORY_EMOJI.get(article.category, "📰")
        status_emoji = cls.STATUS_EMOJI.get(article.status, "")
        
        lines = [
            f"{emoji} <b>{cls._escape_html(article.title)}</b>",
            "",
        ]
        
        # Description or content preview
        text = article.content_clean or article.description or ""
        if text:
            preview = text[:300] + "..." if len(text) > 300 else text
            if include_content:
                preview = text[:1000] + "..." if len(text) > 1000 else text
            lines.append(cls._escape_html(preview))
            lines.append("")
        
        # Meta info
        meta = []
        if article.category:
            meta.append(f"📁 {article.category}")
        if article.source:
            meta.append(f"📡 {article.source.name}")
        if article.pub_date:
            meta.append(f"📅 {article.pub_date.strftime('%d.%m.%Y %H:%M')}")
        
        if meta:
            lines.append(" | ".join(meta))
        
        # Scores
        if include_scores:
            lines.append("")
            lines.append(f"📊 Качество: {article.quality_score:.0%} | Приоритет: {article.priority_score}")
        
        # Status
        lines.append("")
        lines.append(f"{status_emoji} Статус: {article.status.value}")
        
        # Link
        lines.append("")
        lines.append(f"🔗 <a href=\"{article.url}\">Источник</a>")
        
        return "\n".join(lines)
    
    @classmethod
    def article_short(cls, article: Article) -> str:
        """Short article preview for lists"""
        emoji = cls.CATEGORY_EMOJI.get(article.category, "📰")
        title = article.title[:60] + "..." if len(article.title) > 60 else article.title
        
        return f"{emoji} {cls._escape_html(title)}"
    
    @classmethod
    def batch_message(cls, articles: List[Article], batch_id: str) -> str:
        """Build batch moderation message"""
        lines = [
            f"📦 <b>Пакет материалов ({len(articles)} шт.)</b>",
            "",
        ]
        
        for i, article in enumerate(articles, 1):
            emoji = cls.CATEGORY_EMOJI.get(article.category, "📰")
            title = article.title[:50] + "..." if len(article.title) > 50 else article.title
            lines.append(f"{i}. {emoji} {cls._escape_html(title)}")
            lines.append(f"   📊 Q: {article.quality_score:.0%} | P: {article.priority_score}")
            lines.append("")
        
        # Summary
        avg_quality = sum(a.quality_score for a in articles) / len(articles)
        lines.append(f"📈 Средн. качество: {avg_quality:.0%}")
        
        return "\n".join(lines)
    
    @classmethod
    def stats_message(cls, stats: Dict[str, Any]) -> str:
        """Build statistics message"""
        lines = [
            "📊 <b>Статистика</b>",
            "",
            f"📥 Всего материалов: {stats.get('total', 0)}",
            f"⏳ В очереди: {stats.get('pending', 0)}",
            f"✅ Одобрено: {stats.get('approved', 0)}",
            f"❌ Отклонено: {stats.get('rejected', 0)}",
            f"📤 Опубликовано: {stats.get('published', 0)}",
            "",
            f"📈 Approval rate: {stats.get('approval_rate', 0):.1%}",
        ]
        
        if stats.get('today'):
            lines.append("")
            lines.append("<b>Сегодня:</b>")
            lines.append(f"  📥 Поступило: {stats['today'].get('incoming', 0)}")
            lines.append(f"  📤 Опубликовано: {stats['today'].get('published', 0)}")
        
        return "\n".join(lines)
    
    @classmethod
    def queue_message(cls, articles: List[Article], total: int) -> str:
        """Build queue overview message"""
        lines = [
            f"📋 <b>Очередь модерации</b> ({total} материалов)",
            "",
        ]
        
        if not articles:
            lines.append("🎉 Очередь пуста!")
        else:
            for article in articles[:10]:
                emoji = cls.CATEGORY_EMOJI.get(article.category, "📰")
                title = article.title[:40] + "..." if len(article.title) > 40 else article.title
                lines.append(f"{emoji} {cls._escape_html(title)}")
                lines.append(f"   Q: {article.quality_score:.0%} | P: {article.priority_score}")
            
            if total > 10:
                lines.append("")
                lines.append(f"... и еще {total - 10} материалов")
        
        return "\n".join(lines)
    
    @classmethod
    def action_result(cls, action: str, article: Article, success: bool, message: str = "") -> str:
        """Build action result message"""
        emoji = "✅" if success else "❌"
        action_text = {
            "approve": "одобрен",
            "reject": "отклонен",
            "publish": "опубликован",
            "schedule": "запланирован",
            "edit": "отредактирован",
        }.get(action, action)
        
        title = article.title[:50] + "..." if len(article.title) > 50 else article.title
        
        lines = [
            f"{emoji} Материал <b>{action_text}</b>",
            "",
            f"📰 {cls._escape_html(title)}",
        ]
        
        if message:
            lines.append("")
            lines.append(message)
        
        return "\n".join(lines)
    
    @classmethod
    def edit_prompt(cls, article: Article) -> str:
        """Prompt for editing article"""
        lines = [
            "✏️ <b>Редактирование материала</b>",
            "",
            f"📰 {cls._escape_html(article.title)}",
            "",
            "Отправьте новый текст для публикации.",
            "Или нажмите «Отмена» для возврата.",
        ]
        
        return "\n".join(lines)
    
    @classmethod
    def edit_preview(cls, new_text: str) -> str:
        """Preview of edited text"""
        lines = [
            "👁 <b>Предпросмотр</b>",
            "",
            cls._escape_html(new_text[:500]),
            "",
            "Выберите действие:",
        ]
        
        return "\n".join(lines)
    
    @classmethod
    def error_message(cls, error: str) -> str:
        """Error message"""
        return f"⚠️ <b>Ошибка</b>\n\n{cls._escape_html(error)}"
    
    @classmethod
    def unauthorized_message(cls) -> str:
        """Unauthorized access message"""
        return (
            "🚫 <b>Доступ запрещен</b>\n\n"
            "Ваш Telegram аккаунт не привязан к системе или у вас нет прав для этого действия.\n\n"
            "Обратитесь к администратору."
        )
    
    @classmethod
    def already_processed(cls, article: Article) -> str:
        """Already processed message"""
        status_emoji = cls.STATUS_EMOJI.get(article.status, "")
        return f"{status_emoji} Этот материал уже обработан: {article.status.value}"
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters"""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
