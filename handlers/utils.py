# handlers/utils.py
"""
Вспомогательные функции для бота «Числяндия».
Версия: Avatar Cache Ready 🖼️
"""

import json
import os
from telegram import Update
from telegram.constants import ParseMode
from core.avatar_cache import get_avatar_cache
from core.logger import log_error


def load_json(filename: str) -> dict:
    """
    Загружает JSON-файл и возвращает данные.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Файл не найден: {filename}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON в {filename}: {e}")
        return {}


def save_json(filename: str, data: dict) -> bool:
    """
    Сохраняет данные в JSON-файл.
    """
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения {filename}: {e}")
        log_error(0, f"save_json error: {e}")
        return False


async def send_character_message(update: Update, character: str, text: str):
    """
    Отправляет сообщение с аватаркой персонажа (из кэша).
    Если аватарка ещё не загрузилась — отправляет только текст.
    """
    cache = get_avatar_cache()
    file_id = cache.get_avatar(character) if cache else None
    
    try:
        if file_id:
            # ✅ Аватарка загружена — отправляем с фото!
            await update.message.reply_photo(
                photo=file_id,
                caption=text,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # ⏳ Аватарка ещё не загрузилась — только текст
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        # Если ошибка — всё равно показываем текст
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        
        user_id = update.effective_user.id if update.effective_user else 0
        log_error(user_id, f"Avatar error for {character}: {e}")


def get_progress_file_path(user_id: int = None) -> str:
    """
    Возвращает путь к файлу прогресса (для обратной совместимости).
    """
    return "data/all_progress.json"