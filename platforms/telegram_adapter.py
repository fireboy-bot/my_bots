# platforms/telegram_adapter.py
"""
Адаптер Telegram для бота «Числяндия».
Оборачивает Telegram Bot API в универсальный интерфейс MessageAdapter.

Версия: 1.1 (Fix: parse_callback_data + isdigit safety) 🤖✅
"""
import logging
from typing import Optional, Dict, Any

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes
from platforms.base_adapter import MessageAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(MessageAdapter):
    """
    Адаптер для платформы Telegram.
    
    Реализует интерфейс MessageAdapter, предоставляя
    единый способ отправки сообщений независимо от платформы.
    """
    
    def __init__(self, bot: Bot, context: Optional[ContextTypes.DEFAULT_TYPE] = None):
        """
        Инициализация адаптера.
        
        Args:
            bot: Экземпляр telegram.Bot
            context: Контекст обработчика (опционально, для доступа к bot_data)
        """
        self.bot = bot
        self.context = context
    
    async def send_message(
        self,
        user_id: str,
        text: str,
        reply_markup: Optional[Any] = None,
        photo: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Отправить сообщение в Telegram.
        
        Поддерживает:
        - Текст с Markdown/HTML форматированием
        - Кнопки (ReplyKeyboardMarkup или InlineKeyboardMarkup)
        - Фото с подписью
        
        Args:
            user_id: ID чата (строка или число)
            text: Текст сообщения
            reply_markup: Клавиатура Telegram
            photo: file_id или URL изображения
            parse_mode: "Markdown", "HTML" или None
            
        Returns:
            bool: True если отправлено успешно
        """
        try:
            # 🔥 БЕЗОПАСНО: конвертируем в строку перед isdigit()
            user_id_str = str(user_id)
            chat_id = int(user_id_str) if user_id_str.isdigit() else user_id_str
            
            if photo:
                # Отправка фото с подписью
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode if parse_mode != "plain" else None,
                    show_caption_above_media=True
                )
            else:
                # Отправка обычного текста
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode if parse_mode != "plain" else None,
                    disable_web_page_preview=True
                )
            logger.debug(f"✅ TG: сообщение отправлено {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ TG send error: {e}", exc_info=True)
            return False
    
    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """
        Редактировать существующее сообщение в Telegram.
        
        Args:
            chat_id: ID чата
            message_id: ID сообщения для редактирования
            text: Новый текст
            reply_markup: Новая клавиатура (опционально)
            
        Returns:
            bool: True если успешно
        """
        try:
            chat_id_str = str(chat_id)
            await self.bot.edit_message_text(
                chat_id=int(chat_id_str) if chat_id_str.isdigit() else chat_id_str,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.debug(f"✅ TG: сообщение отредактировано {chat_id}:{message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ TG edit error: {e}")
            return False
    
    def parse_callback_data(self,  str) -> Dict[str, str]:
        """
        Распарсить callback_data от Telegram.
        
        Формат: "action:param1:value1|param2:value2"
        Пример: "buy_item:id:potion_health|qty:1"
        
        Args:
            data: Сырая строка callback_data
            
        Returns:
            Dict: {параметр: значение}
        """
        result = {}
        
        # Разбиваем по |
        parts = data.split("|")
        for part in parts:
            if ":" in part:
                # Первый : разделяет ключ и значение
                key, _, value = part.partition(":")
                result[key.strip()] = value.strip()
        
        # Если нет : — считаем всю строку действием
        if not result and data:
            result["action"] = data
        
        return result
    
    def normalize_user_id(self, raw_id: Any) -> str:
        """
        Привести Telegram user_id к строковому формату.
        
        Telegram использует int (например, 5001966771),
        но мы храним все ID как строки для совместимости с MAX.
        
        Args:
            raw_id: int или стр
            
        Returns:
            str: Универсальный ID
        """
        # 🔍 ОТЛАДКА: логируем что приходит
        logger.info(f"🔍 normalize_user_id: raw={raw_id} (type={type(raw_id).__name__}) -> str={str(raw_id)}")
        return str(raw_id)
    
    @property
    def platform_name(self) -> str:
        """Название платформы"""
        return "telegram"
    
    async def close(self):
        """Закрыть соединения (для Telegram не требуется)"""
        logger.info("🔌 TelegramAdapter closed")
        pass