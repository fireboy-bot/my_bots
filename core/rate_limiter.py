# core/rate_limiter.py
"""
Простой rate limiter для хендлеров бота.
Ограничивает частоту вызовов по user_id.
"""

import time
import logging
from functools import wraps
from typing import Optional, Callable
from telegram.ext import ContextTypes
from telegram import Update

# Хранилище: {user_id: timestamp_last_call}
_rate_limit_store: dict[int, float] = {}

# Логгер
logger = logging.getLogger(__name__)

def rate_limit(limit_seconds: float = 1.0, message: Optional[str] = None):
    """
    Декоратор для ограничения частоты вызовов хендлера.
    
    Args:
        limit_seconds: Минимальный интервал между вызовами (сек)
        message: Сообщение пользователю при превышении лимита
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else 0
            now = time.time()
            
            last_call = _rate_limit_store.get(user_id, 0)
            time_diff = now - last_call
            
            # ✅ ЛОГИРУЕМ для отладки
            logger.info(f"Rate limit check: user={user_id}, func={func.__name__}, diff={time_diff:.2f}s, limit={limit_seconds}s")
            
            if time_diff < limit_seconds:
                # Лимит превышен
                logger.warning(f"Rate limit EXCEEDED: user={user_id}, func={func.__name__}")
                if message and update.message:
                    await update.message.reply_text(message)
                return None  # ✅ Явно возвращаем None
            # Обновляем timestamp
            _rate_limit_store[user_id] = now
            logger.info(f"Rate limit OK: user={user_id}, func={func.__name__}")
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator