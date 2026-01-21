from typing import Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ModerationKeyboard:
    """Keyboard builder for moderation actions"""
    
    @staticmethod
    def article_actions(token: str, show_edit: bool = True) -> InlineKeyboardMarkup:
        """Keyboard for single article moderation"""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"a:{token}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"r:{token}"),
            ]
        ]
        
        if show_edit:
            buttons.append([
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"e:{token}"),
            ])
        
        buttons.append([
            InlineKeyboardButton(text="📊 Подробнее", callback_data=f"d:{token}"),
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def batch_actions(batch_id: str) -> InlineKeyboardMarkup:
        """Keyboard for batch moderation"""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Одобрить все", callback_data=f"aa:{batch_id}"),
                InlineKeyboardButton(text="❌ Отклонить все", callback_data=f"ra:{batch_id}"),
            ],
            [
                InlineKeyboardButton(text="📋 По одному", callback_data=f"one:{batch_id}"),
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def article_detail(token: str) -> InlineKeyboardMarkup:
        """Keyboard for article detail view"""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"a:{token}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"r:{token}"),
            ],
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"e:{token}"),
                InlineKeyboardButton(text="🔄 AI Рерайт", callback_data=f"ai:{token}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back:{token}"),
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def edit_confirm(token: str) -> InlineKeyboardMarkup:
        """Keyboard for edit confirmation"""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Сохранить и опубликовать", callback_data=f"ep:{token}"),
                InlineKeyboardButton(text="💾 Только сохранить", callback_data=f"es:{token}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"ec:{token}"),
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def reject_reasons() -> InlineKeyboardMarkup:
        """Keyboard for rejection reason selection"""
        reasons = [
            ("🔄 Дубликат", "reason:duplicate"),
            ("📉 Низкое качество", "reason:low_quality"),
            ("🚫 Неактуально", "reason:irrelevant"),
            ("⚠️ Неподходящий контент", "reason:inappropriate"),
            ("📝 Другое", "reason:other"),
        ]
        
        buttons = [[InlineKeyboardButton(text=text, callback_data=data)] for text, data in reasons]
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="reason:cancel")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def schedule_options(token: str) -> InlineKeyboardMarkup:
        """Keyboard for scheduling options"""
        buttons = [
            [
                InlineKeyboardButton(text="⏰ Через 1 час", callback_data=f"sch:1h:{token}"),
                InlineKeyboardButton(text="⏰ Через 3 часа", callback_data=f"sch:3h:{token}"),
            ],
            [
                InlineKeyboardButton(text="📅 Завтра утром", callback_data=f"sch:tom:{token}"),
                InlineKeyboardButton(text="📅 Завтра вечером", callback_data=f"sch:eve:{token}"),
            ],
            [
                InlineKeyboardButton(text="🚀 Опубликовать сейчас", callback_data=f"a:{token}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back:{token}"),
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        buttons = [
            [
                InlineKeyboardButton(text="📋 Очередь", callback_data="menu:queue"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats"),
            ],
            [
                InlineKeyboardButton(text="⏰ Запланированные", callback_data="menu:scheduled"),
                InlineKeyboardButton(text="📰 Последние", callback_data="menu:recent"),
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
