# handlers/narrative_manager.py
"""
Менеджер нарратива — фразы персонажей, аватарки, контексты.
Версия: 3.4 (Fix: user_data: Dict + context.bot_data) 🎩🫖✅
"""

import json
import random
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# === ПЕРСОНАЖИ ===
CHARACTERS = {
    "manunya": {"name": "Манюня", "avatar": "manunya.jpg", "role": "guide"},
    "georgy": {"name": "Георгий", "avatar": "georgy.jpg", "role": "friend"},
    "vladimir": {"name": "Владимир", "avatar": None, "role": "butler"},
    "shop_keeper": {"name": "Торговец", "avatar": "shop_keeper.jpg", "role": "merchant"},
    "alchemist": {"name": "Алхимик", "avatar": "alchemist_mad.jpg", "role": "alchemist"}
}

# === АВАТАРКИ ВЛАДИМИРА ===
# ✅ ВРЕМЕННО: все настроения → vladimir_calm.jpg
VLADIMIR_MOODS = {
    "calm": "vladimir_calm.jpg",
    "approve": "vladimir_calm.jpg",
    "disappointed": "vladimir_calm.jpg",
    "proud": "vladimir_calm.jpg",
    "thinking": "vladimir_calm.jpg",
    "relaxed": "vladimir_calm.jpg",
}


class PhraseManager:
    def __init__(self, phrases_path: str = "data/vladimir_phrases.json"):
        self.phrases_path = Path(phrases_path)
        self.vladimir_phrases: Dict = {}
        self._load_vladimir_phrases()
    
    def _load_vladimir_phrases(self):
        if self.phrases_path.exists():
            try:
                with open(self.phrases_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.vladimir_phrases = data.get("vladimir", {})
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки фраз Владимира: {e}")
                self.vladimir_phrases = {}
        else:
            logger.warning(f"⚠️ Файл {self.phrases_path} не найден")
            self.vladimir_phrases = {}
    
    def get_vladimir_phrase(self, context: str, **kwargs) -> str:
        phrases = self.vladimir_phrases.get(context, [])
        if not phrases:
            return "🎩 «Я к Вашим услугам, сударыня.»"
        phrase = random.choice(phrases)
        if kwargs:
            try:
                phrase = phrase.format(**kwargs)
            except KeyError:
                pass
        return phrase
    
    def is_castle_unlocked(self, user_data: Dict) -> bool:
        defeated_bosses = user_data.get("defeated_bosses", [])
        completed_normal = user_data.get("completed_normal_game", False)
        return "final_boss" in defeated_bosses or completed_normal
    
    def get_castle_access_level(self, user_data: Dict) -> str:
        if self.is_castle_unlocked(user_data):
            return "full"
        elif user_data.get("level", 1) >= 5:
            return "preview"
        else:
            return "locked"


# === ОТПРАВКА СООБЩЕНИЙ С АВАТАРКОЙ ===
async def send_character_message(
    update,
    context,
    character: str,
    text: str,
    mood: str = "calm",
    parse_mode: str = "HTML"
):
    """
    Отправляет сообщение от имени персонажа с аватаркой.
    ✅ ИСПРАВЛЕНО: context.bot_data вместо update.bot_data
    """
    from telegram import InputFile
    
    logger.info(f"🎬 send_character_message ВЫЗВАН: character={character}, mood={mood}, text={text[:30]}...")
    
    adapter = context.bot_data.get('adapter') if context and context.bot_data else None
    if not adapter:
        logger.warning(f"⚠️ Adapter not found in context.bot_data, fallback to text")
        await update.message.reply_text(text, parse_mode=parse_mode)
        return
    
    logger.info(f"✅ Adapter получен из context.bot_data")
    
    avatar_cache = None
    try:
        from core.avatar_cache import get_avatar_cache
        avatar_cache = get_avatar_cache()
        logger.info(f"🗄️ AvatarCache получен: {avatar_cache is not None}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить avatar_cache: {e}")
    
    if character == "vladimir":
        avatar_name = VLADIMIR_MOODS.get(mood, "vladimir_calm.jpg")
    else:
        char_config = CHARACTERS.get(character, {})
        avatar_name = char_config.get("avatar", "manunya.jpg")
    
    logger.info(f"🖼️ Avatar name: {avatar_name}")
    
    file_id = None
    if avatar_cache and avatar_name:
        cache_key = avatar_name.replace(".jpg", "")
        file_id = avatar_cache.get_avatar(cache_key)
        logger.info(f"🔍 Cache lookup: key={cache_key}, file_id={'✅' if file_id else '❌'}")
    
    if file_id:
        try:
            logger.info(f"📤 Отправка фото из кэша: {cache_key}")
            await update.message.reply_photo(
                photo=file_id,
                caption=text,
                parse_mode=parse_mode
            )
            logger.info(f"✅ Фото отправлено из кэша: {cache_key}")
            return
        except Exception as e:
            logger.warning(f"⚠️ Ошибка отправки фото из кэша: {e}")
    
    if avatar_name:
        avatar_path = Path("images") / avatar_name
        logger.info(f"📂 Проверка локального файла: {avatar_path} → {avatar_path.exists()}")
        if avatar_path.exists():
            try:
                logger.info(f"📤 Отправка локального фото: {avatar_name}")
                await update.message.reply_photo(
                    photo=InputFile(str(avatar_path)),
                    caption=text,
                    parse_mode=parse_mode
                )
                logger.info(f"✅ Локальное фото отправлено: {avatar_name}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Ошибка отправки локального фото: {e}")
    
    logger.info(f"⚠️ FALLBACK НА ТЕКСТ для {character}")
    await update.message.reply_text(text, parse_mode=parse_mode)


# === ОТПРАВКА ПО USER_ID (ДЛЯ КАТ-СЦЕН) ===
async def send_character_message_by_id(
    user_id: str, 
    text: str, 
    character: str, 
    mood: str, 
    context
):
    """
    Отправка сообщения от персонажа по user_id (для кат-сцен).
    """
    logger.info(f"🎬 send_character_message_by_id ВЫЗВАН: character={character}, mood={mood}, user_id={user_id}")
    
    adapter = context.bot_data.get('adapter') if context and context.bot_data else None
    if not adapter:
        logger.warning(f"⚠️ Adapter not found")
        return
    
    logger.info(f"✅ Adapter получен из context.bot_data")
    
    avatar_cache = None
    try:
        from core.avatar_cache import get_avatar_cache
        avatar_cache = get_avatar_cache()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить avatar_cache: {e}")
    
    if character == "vladimir":
        avatar_name = VLADIMIR_MOODS.get(mood, "vladimir_calm.jpg")
    else:
        char_config = CHARACTERS.get(character, {})
        avatar_name = char_config.get("avatar", "manunya.jpg")
    
    logger.info(f"🖼️ Avatar name: {avatar_name}")
    
    file_id = None
    if avatar_cache and avatar_name:
        cache_key = avatar_name.replace(".jpg", "")
        file_id = avatar_cache.get_avatar(cache_key)
        logger.info(f"🔍 Cache lookup: key={cache_key}, file_id={'✅' if file_id else '❌'}")
    
    if file_id:
        try:
            logger.info(f"📤 Отправка фото из кэша: {cache_key}")
            await adapter.bot.send_photo(
                chat_id=user_id,
                photo=file_id,
                caption=text,
                parse_mode="HTML"
            )
            logger.info(f"✅ Фото отправлено из кэша: {cache_key}")
            return
        except Exception as e:
            logger.warning(f"⚠️ Ошибка отправки фото из кэша: {e}")
    
    if avatar_name:
        avatar_path = Path("images") / avatar_name
        if avatar_path.exists():
            try:
                from telegram import InputFile
                logger.info(f"📤 Отправка локального фото: {avatar_name}")
                await adapter.bot.send_photo(
                    chat_id=user_id,
                    photo=InputFile(str(avatar_path)),
                    caption=text,
                    parse_mode="HTML"
                )
                logger.info(f"✅ Локальное фото отправлено: {avatar_name}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Ошибка отправки локального фото: {e}")
    
    logger.info(f"⚠️ FALLBACK НА ТЕКСТ для {character}")
    await adapter.send_message(user_id=user_id, text=text, parse_mode="HTML")


__all__ = [
    "CHARACTERS",
    "VLADIMIR_MOODS",
    "PhraseManager",
    "send_character_message",
    "send_character_message_by_id",
]