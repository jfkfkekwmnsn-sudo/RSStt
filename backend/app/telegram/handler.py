from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot
from aiogram.types import Update, CallbackQuery, Message

from app.config import settings
from app.models.user import User, UserRole
from app.models.article import Article, ArticleStatus
from app.models.batch import Batch
from app.telegram.keyboards import ModerationKeyboard
from app.telegram.messages import MessageBuilder
from app.services.moderation_service import ModerationService
from app.services.article_service import ArticleService
from app.services.analytics_service import AnalyticsService
from app.utils.redis import get_redis
import structlog

logger = structlog.get_logger()


class TelegramHandler:
    """Handler for Telegram webhook updates"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
        self.moderation = ModerationService(db)
        self.articles = ArticleService(db)
        self.analytics = AnalyticsService(db)
    
    async def process_update(self, update_data: Dict[str, Any]):
        """Process incoming Telegram update"""
        update = Update(**update_data)
        
        if update.callback_query:
            await self._handle_callback(update.callback_query)
        elif update.message:
            await self._handle_message(update.message)
    
    async def _handle_callback(self, callback: CallbackQuery):
        """Handle callback query from inline buttons"""
        user = await self._get_authorized_user(callback.from_user.id)
        
        if not user:
            await callback.answer("Доступ запрещен", show_alert=True)
            return
        
        data = callback.data
        logger.info("Callback received", user_id=user.id, data=data)
        
        try:
            # Parse callback data
            parts = data.split(":")
            action = parts[0]
            
            # Route to handler
            handlers = {
                "a": self._handle_approve,
                "r": self._handle_reject,
                "e": self._handle_edit_start,
                "d": self._handle_detail,
                "ai": self._handle_ai_rewrite,
                "aa": self._handle_approve_all,
                "ra": self._handle_reject_all,
                "sch": self._handle_schedule,
                "ep": self._handle_edit_publish,
                "es": self._handle_edit_save,
                "ec": self._handle_edit_cancel,
                "back": self._handle_back,
                "reason": self._handle_reject_reason,
                "menu": self._handle_menu,
                "stats": self._handle_stats,
            }
            
            handler = handlers.get(action)
            if handler:
                await handler(callback, user, parts[1:])
            else:
                await callback.answer("Неизвестное действие")
                
        except Exception as e:
            logger.error("Callback handling error", error=str(e))
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    
    async def _handle_message(self, message: Message):
        """Handle text messages (commands or edit text)"""
        user = await self._get_authorized_user(message.from_user.id)
        
        if not user:
            await message.reply(MessageBuilder.unauthorized_message(), parse_mode="HTML")
            return
        
        text = message.text or ""
        
        # Check for commands
        if text.startswith("/"):
            await self._handle_command(message, user, text)
            return
        
        # Check for edit state
        redis = await get_redis()
        edit_state = await redis.get(f"edit_state:{message.from_user.id}")
        
        if edit_state:
            await self._handle_edit_text(message, user, edit_state.decode())
            return
        
        # Default response
        await message.reply(
            "Используйте команды или кнопки для работы с системой.\n"
            "Отправьте /help для списка команд.",
            parse_mode="HTML"
        )
    
    async def _handle_command(self, message: Message, user: User, text: str):
        """Handle bot commands"""
        command = text.split()[0].lower()
        
        if command == "/start":
            await message.reply(
                f"👋 Привет, {user.username}!\n\n"
                f"Вы авторизованы как <b>{user.role.value}</b>.\n\n"
                "Используйте меню для работы с материалами.",
                parse_mode="HTML",
                reply_markup=ModerationKeyboard.main_menu()
            )
        
        elif command == "/help":
            await message.reply(
                "📖 <b>Доступные команды:</b>\n\n"
                "/start - Главное меню\n"
                "/queue - Очередь модерации\n"
                "/stats - Статистика\n"
                "/next - Следующий материал\n"
                "/help - Эта справка",
                parse_mode="HTML"
            )
        
        elif command == "/queue":
            await self._send_queue(message, user)
        
        elif command == "/stats":
            await self._send_stats(message, user)
        
        elif command == "/next":
            await self._send_next_article(message, user)
        
        else:
            await message.reply("Неизвестная команда. Отправьте /help для списка команд.")
    
    async def _get_authorized_user(self, telegram_user_id: int) -> Optional[User]:
        """Get authorized user by Telegram ID"""
        query = select(User).where(
            User.telegram_user_id == telegram_user_id,
            User.is_active == True,
            User.role.in_([UserRole.ADMIN, UserRole.EDITOR, UserRole.CHIEF_EDITOR])
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_article_by_token(self, token: str) -> Optional[Article]:
        """Get article by public token"""
        query = select(Article).where(Article.token == token)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _handle_approve(self, callback: CallbackQuery, user: User, args: list):
        """Handle article approval"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        if article.status != ArticleStatus.PENDING:
            await callback.answer(f"Материал уже обработан: {article.status.value}")
            await callback.message.edit_text(
                MessageBuilder.already_processed(article),
                parse_mode="HTML"
            )
            return
        
        result = await self.moderation.approve_article(
            article_id=article.id,
            user_id=user.id
        )
        
        if result["success"]:
            await callback.answer("✅ Одобрено")
            await callback.message.edit_text(
                MessageBuilder.action_result("approve", article, True, "Материал отправлен на публикацию"),
                parse_mode="HTML"
            )
        else:
            await callback.answer(f"Ошибка: {result['message']}", show_alert=True)
    
    async def _handle_reject(self, callback: CallbackQuery, user: User, args: list):
        """Handle article rejection - show reason selection"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        if article.status != ArticleStatus.PENDING:
            await callback.answer(f"Материал уже обработан: {article.status.value}")
            return
        
        # Store article token for reason selection
        redis = await get_redis()
        await redis.setex(f"reject_article:{callback.from_user.id}", 300, token)
        
        await callback.message.edit_text(
            f"❌ <b>Отклонение материала</b>\n\n"
            f"📰 {article.title[:100]}\n\n"
            f"Выберите причину отклонения:",
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.reject_reasons()
        )
        await callback.answer()
    
    async def _handle_reject_reason(self, callback: CallbackQuery, user: User, args: list):
        """Handle rejection reason selection"""
        reason_key = args[0] if args else None
        
        if reason_key == "cancel":
            # Return to article
            redis = await get_redis()
            token = await redis.get(f"reject_article:{callback.from_user.id}")
            if token:
                article = await self._get_article_by_token(token.decode())
                if article:
                    await callback.message.edit_text(
                        MessageBuilder.article_card(article),
                        parse_mode="HTML",
                        reply_markup=ModerationKeyboard.article_actions(article.token)
                    )
            await callback.answer()
            return
        
        redis = await get_redis()
        token = await redis.get(f"reject_article:{callback.from_user.id}")
        
        if not token:
            await callback.answer("Сессия истекла")
            return
        
        article = await self._get_article_by_token(token.decode())
        if not article:
            await callback.answer("Материал не найден")
            return
        
        reasons = {
            "duplicate": "Дубликат",
            "low_quality": "Низкое качество",
            "irrelevant": "Неактуально",
            "inappropriate": "Неподходящий контент",
            "other": "Другое",
        }
        
        reason = reasons.get(reason_key, reason_key)
        
        result = await self.moderation.reject_article(
            article_id=article.id,
            user_id=user.id,
            reason=reason
        )
        
        await redis.delete(f"reject_article:{callback.from_user.id}")
        
        if result["success"]:
            await callback.answer("❌ Отклонено")
            await callback.message.edit_text(
                MessageBuilder.action_result("reject", article, True, f"Причина: {reason}"),
                parse_mode="HTML"
            )
        else:
            await callback.answer(f"Ошибка: {result['message']}", show_alert=True)
    
    async def _handle_edit_start(self, callback: CallbackQuery, user: User, args: list):
        """Start editing article"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        # Store edit state
        redis = await get_redis()
        await redis.setex(f"edit_state:{callback.from_user.id}", 600, token)
        
        await callback.message.edit_text(
            MessageBuilder.edit_prompt(article),
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.edit_confirm(token)
        )
        await callback.answer("Отправьте новый текст")
    
    async def _handle_edit_text(self, message: Message, user: User, token: str):
        """Handle edited text from user"""
        article = await self._get_article_by_token(token)
        if not article:
            await message.reply("Материал не найден")
            return
        
        new_text = message.text
        
        # Store new text
        redis = await get_redis()
        await redis.setex(f"edit_text:{message.from_user.id}", 600, new_text)
        
        await message.reply(
            MessageBuilder.edit_preview(new_text),
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.edit_confirm(token)
        )
    
    async def _handle_edit_publish(self, callback: CallbackQuery, user: User, args: list):
        """Save edit and publish"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        redis = await get_redis()
        new_text = await redis.get(f"edit_text:{callback.from_user.id}")
        
        if new_text:
            # Update article
            from app.schemas.article import ArticleUpdate
            await self.articles.update_article(
                article_id=article.id,
                data=ArticleUpdate(content_clean=new_text.decode()),
                user_id=user.id
            )
        
        # Approve
        result = await self.moderation.approve_article(
            article_id=article.id,
            user_id=user.id
        )
        
        # Clean up
        await redis.delete(f"edit_state:{callback.from_user.id}")
        await redis.delete(f"edit_text:{callback.from_user.id}")
        
        if result["success"]:
            await callback.answer("✅ Сохранено и опубликовано")
            await callback.message.edit_text(
                MessageBuilder.action_result("edit", article, True, "Материал отредактирован и отправлен на публикацию"),
                parse_mode="HTML"
            )
        else:
            await callback.answer(f"Ошибка: {result['message']}", show_alert=True)
    
    async def _handle_edit_save(self, callback: CallbackQuery, user: User, args: list):
        """Save edit without publishing"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        redis = await get_redis()
        new_text = await redis.get(f"edit_text:{callback.from_user.id}")
        
        if new_text:
            from app.schemas.article import ArticleUpdate
            await self.articles.update_article(
                article_id=article.id,
                data=ArticleUpdate(content_clean=new_text.decode()),
                user_id=user.id
            )
        
        # Clean up
        await redis.delete(f"edit_state:{callback.from_user.id}")
        await redis.delete(f"edit_text:{callback.from_user.id}")
        
        await callback.answer("💾 Сохранено")
        await callback.message.edit_text(
            MessageBuilder.article_card(article),
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.article_actions(token)
        )
    
    async def _handle_edit_cancel(self, callback: CallbackQuery, user: User, args: list):
        """Cancel editing"""
        token = args[0] if args else None
        
        redis = await get_redis()
        await redis.delete(f"edit_state:{callback.from_user.id}")
        await redis.delete(f"edit_text:{callback.from_user.id}")
        
        if token:
            article = await self._get_article_by_token(token)
            if article:
                await callback.message.edit_text(
                    MessageBuilder.article_card(article),
                    parse_mode="HTML",
                    reply_markup=ModerationKeyboard.article_actions(token)
                )
        
        await callback.answer("Редактирование отменено")
    
    async def _handle_detail(self, callback: CallbackQuery, user: User, args: list):
        """Show article details"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        await callback.message.edit_text(
            MessageBuilder.article_card(article, include_content=True, include_scores=True),
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.article_detail(token)
        )
        await callback.answer()
    
    async def _handle_back(self, callback: CallbackQuery, user: User, args: list):
        """Go back to article card"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        await callback.message.edit_text(
            MessageBuilder.article_card(article),
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.article_actions(token)
        )
        await callback.answer()
    
    async def _handle_ai_rewrite(self, callback: CallbackQuery, user: User, args: list):
        """Apply AI rewrite"""
        token = args[0] if args else None
        if not token:
            await callback.answer("Неверные данные")
            return
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        await callback.answer("🔄 Применяем AI...")
        
        result = await self.articles.apply_ai_rewrite(
            article_id=article.id,
            user_id=user.id
        )
        
        if result:
            await callback.message.edit_text(
                MessageBuilder.article_card(result, include_content=True),
                parse_mode="HTML",
                reply_markup=ModerationKeyboard.article_detail(token)
            )
        else:
            await callback.answer("Ошибка AI", show_alert=True)
    
    async def _handle_approve_all(self, callback: CallbackQuery, user: User, args: list):
        """Approve all articles in batch"""
        batch_id = args[0] if args else None
        if not batch_id:
            await callback.answer("Неверные данные")
            return
        
        result = await self.moderation.approve_batch(
            batch_id=UUID(batch_id),
            user_id=user.id
        )
        
        await callback.answer(f"✅ Одобрено: {result.get('approved_count', 0)}")
        await callback.message.edit_text(
            f"✅ Пакет одобрен\n\n"
            f"Одобрено материалов: {result.get('approved_count', 0)}",
            parse_mode="HTML"
        )
    
    async def _handle_reject_all(self, callback: CallbackQuery, user: User, args: list):
        """Reject all articles in batch"""
        batch_id = args[0] if args else None
        if not batch_id:
            await callback.answer("Неверные данные")
            return
        
        result = await self.moderation.reject_batch(
            batch_id=UUID(batch_id),
            user_id=user.id,
            reason="Пакетное отклонение"
        )
        
        await callback.answer(f"❌ Отклонено: {result.get('rejected_count', 0)}")
        await callback.message.edit_text(
            f"❌ Пакет отклонен\n\n"
            f"Отклонено материалов: {result.get('rejected_count', 0)}",
            parse_mode="HTML"
        )
    
    async def _handle_schedule(self, callback: CallbackQuery, user: User, args: list):
        """Handle scheduling"""
        if len(args) < 2:
            await callback.answer("Неверные данные")
            return
        
        time_option = args[0]
        token = args[1]
        
        article = await self._get_article_by_token(token)
        if not article:
            await callback.answer("Материал не найден")
            return
        
        # Calculate schedule time
        now = datetime.now()
        schedule_times = {
            "1h": now + timedelta(hours=1),
            "3h": now + timedelta(hours=3),
            "tom": (now + timedelta(days=1)).replace(hour=9, minute=0, second=0),
            "eve": (now + timedelta(days=1)).replace(hour=18, minute=0, second=0),
        }
        
        scheduled_at = schedule_times.get(time_option)
        if not scheduled_at:
            await callback.answer("Неверное время")
            return
        
        result = await self.moderation.schedule_article(
            article_id=article.id,
            user_id=user.id,
            scheduled_at=scheduled_at
        )
        
        if result["success"]:
            await callback.answer("⏰ Запланировано")
            await callback.message.edit_text(
                f"⏰ Материал запланирован\n\n"
                f"📰 {article.title[:100]}\n\n"
                f"📅 Время публикации: {scheduled_at.strftime('%d.%m.%Y %H:%M')} UTC",
                parse_mode="HTML"
            )
        else:
            await callback.answer(f"Ошибка: {result['message']}", show_alert=True)
    
    async def _handle_menu(self, callback: CallbackQuery, user: User, args: list):
        """Handle menu actions"""
        action = args[0] if args else None
        
        if action == "queue":
            await self._send_queue(callback.message, user, edit=True)
        elif action == "stats":
            await self._send_stats(callback.message, user, edit=True)
        elif action == "scheduled":
            await self._send_scheduled(callback.message, user, edit=True)
        elif action == "recent":
            await self._send_recent(callback.message, user, edit=True)
        
        await callback.answer()
    
    async def _handle_stats(self, callback: CallbackQuery, user: User, args: list):
        """Show stats"""
        await self._send_stats(callback.message, user, edit=True)
        await callback.answer()
    
    async def _send_queue(self, message: Message, user: User, edit: bool = False):
        """Send queue overview"""
        articles, total = await self.articles.get_moderation_queue(page=1, per_page=10)
        text = MessageBuilder.queue_message(articles, total)
        
        if edit:
            await message.edit_text(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
        else:
            await message.reply(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
    
    async def _send_stats(self, message: Message, user: User, edit: bool = False):
        """Send statistics"""
        stats = await self.analytics.get_summary_stats()
        text = MessageBuilder.stats_message(stats)
        
        if edit:
            await message.edit_text(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
        else:
            await message.reply(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
    
    async def _send_scheduled(self, message: Message, user: User, edit: bool = False):
        """Send scheduled articles"""
        from app.models.article import ArticleStatus
        
        query = select(Article).where(
            Article.status == ArticleStatus.SCHEDULED
        ).order_by(Article.scheduled_at).limit(10)
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        if not articles:
            text = "⏰ <b>Запланированные публикации</b>\n\n🎉 Нет запланированных публикаций"
        else:
            lines = ["⏰ <b>Запланированные публикации</b>\n"]
            for article in articles:
                time_str = article.scheduled_at.strftime('%d.%m %H:%M') if article.scheduled_at else "?"
                lines.append(f"📅 {time_str} - {article.title[:40]}...")
            text = "\n".join(lines)
        
        if edit:
            await message.edit_text(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
        else:
            await message.reply(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
    
    async def _send_recent(self, message: Message, user: User, edit: bool = False):
        """Send recent published articles"""
        query = select(Article).where(
            Article.status == ArticleStatus.PUBLISHED
        ).order_by(Article.published_at.desc()).limit(10)
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        if not articles:
            text = "📤 <b>Последние публикации</b>\n\n📭 Пока нет публикаций"
        else:
            lines = ["📤 <b>Последние публикации</b>\n"]
            for article in articles:
                time_str = article.published_at.strftime('%d.%m %H:%M') if article.published_at else "?"
                lines.append(f"✅ {time_str} - {article.title[:40]}...")
            text = "\n".join(lines)
        
        if edit:
            await message.edit_text(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
        else:
            await message.reply(text, parse_mode="HTML", reply_markup=ModerationKeyboard.main_menu())
    
    async def _send_next_article(self, message: Message, user: User):
        """Send next article from queue for moderation"""
        articles, total = await self.articles.get_moderation_queue(page=1, per_page=1)
        
        if not articles:
            await message.reply(
                "🎉 Очередь пуста! Все материалы обработаны.",
                parse_mode="HTML",
                reply_markup=ModerationKeyboard.main_menu()
            )
            return
        
        article = articles[0]
        await message.reply(
            MessageBuilder.article_card(article),
            parse_mode="HTML",
            reply_markup=ModerationKeyboard.article_actions(article.token)
        )
