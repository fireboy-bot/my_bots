# handlers/vladimir_appearance.py
"""
Появление Владимира после прохождения 4 островов.
Версия: 1.0 (Mystery Introduction) 😈✨

Сценарий:
- Вызывается после победы над Дробозавром (4-й босс)
- Владимир появляется БЕЗ имени (игрок сам додумывает)
- Манюня реагирует но НЕ объясняет кто это
- Замок начинает "оживать" после этого
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def trigger_vladimir_first_appearance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Триггер первого появления Владимира.
    Вызывается после победы над 4-м боссом (Дробозавр).
    
    Важно:
    - Не называем Владимира по имени (интрига!)
    - Манюня реагирует но не объясняет
    - Игрок должен сам додумать кто это
    """
    logger.info(f"😈 Триггер появления Владимира для user_id={update.effective_user.id if update.effective_user else 'unknown'}")
    
    adapter = context.bot_data.get('adapter')
    if not adapter:
        logger.error("❌ Adapter не найден!")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    try:
        # === СЦЕНА 1: АТМОСФЕРА ===
        await adapter.send_message(
            user_id=user_id,
            text="…\n\n*Что-то меняется…*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        # === СЦЕНА 2: МИР ЗАМИРАЕТ ===
        await adapter.send_message(
            user_id=user_id,
            text="*Мир замирает.*\n\n"
                 "Даже числа…\n"
                 "перестают двигаться.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        # === СЦЕНА 3: ПОЯВЛЯЕТСЯ СООБЩЕНИЕ ===
        await adapter.send_message(
            user_id=user_id,
            text="…\n\n"
                 "*Появляется сообщение.*\n\n"
                 "Не от Манюни.\n"
                 "Не из интерфейса.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        # === СЦЕНА 4: ВЛАДИМИР ГОВОРИТ (БЕЗ ИМЕНИ!) ===
        await adapter.send_message(
            user_id=user_id,
            text="*«Любопытно.»*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        await adapter.send_message(
            user_id=user_id,
            text="*«Ты прошёл так далеко.»*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        await adapter.send_message(
            user_id=user_id,
            text="*«И при этом…»*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        await adapter.send_message(
            user_id=user_id,
            text="*«Ты всё ещё считаешь, что просто решаешь задачи?»*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        # === СЦЕНА 5: ПАУЗА ===
        await adapter.send_message(
            user_id=user_id,
            text="…",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        # === СЦЕНА 6: ПРИЗЫВ ===
        await adapter.send_message(
            user_id=user_id,
            text="*«Продолжай.»*\n\n"
                 "*«Мне интересно, когда ты начнёшь понимать.»*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.5)
        
        # === СЦЕНА 7: РЕАКЦИЯ МАНЮНИ (НЕ ОБЪЯСНЯЕТ!) ===
        await adapter.send_message(
            user_id=user_id,
            text="🧚‍♀️ *Манюня*:\n\n"
                 "«Эм…\n"
                 "Ты это видела?\n"
                 "Мне это… не нравится…»",
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Владимир появился для user_id={user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при появлении Владимира: {e}")
    
    # ✅ ПОМЕТКА: Владимир появился (чтобы не показывать дважды)
    storage = context.bot_data.get('storage')
    if storage:
        try:
            user_data = storage.get_user(user_id)
            if user_
                user_data["vladimir_appeared"] = True
                user_data["vladimir_appeared_at"] = asyncio.get_event_loop().time()
                storage.save_user(user_id, user_data)
                logger.info(f"💾 Сохранено: vladimir_appeared=True для user_id={user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения флага Владимира: {e}")


async def trigger_vladimir_castle_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Случайная фраза Владимира в замке (после его появления).
    Вызывается из handlers/castle.py при входе в замок.
    """
    adapter = context.bot_data.get('adapter')
    if not adapter:
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    # Фразы Владимира для замка (разные уровни "оживания")
    castle_phrases = [
        "«Замок помнит тех, кто видит дальше чисел.»",
        "«Вы обрели ключ. Но дверь ещё закрыта.»",
        "«Любопытно… что вы сделаете дальше?»",
        "«Стены слышали многое. Но не всё скажут.»",
        "«Вы ближе чем думаете. Но не так близки как кажется.»",
    ]
    
    import random
    phrase = random.choice(castle_phrases)
    
    try:
        await adapter.send_message(
            user_id=user_id,
            text=f"🎩 *???:*\n\n{phrase}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка фразы Владимира в замке: {e}")