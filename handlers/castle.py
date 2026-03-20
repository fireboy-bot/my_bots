# handlers/castle.py
"""
Хендлеры Замка — декорации, upkeep, ВладимИр.
Версия: 5.7 (Clean + Secret Room Button FIX) 🏰🎩🫖🗝️✅
"""

import logging
import json
from typing import Dict
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from core.logger import log_user_action
from items import CASTLE_DECORATIONS
from handlers.narrative_manager import PhraseManager, send_character_message, send_character_message_by_id

logger = logging.getLogger(__name__)

# ✅ Инициализируем PhraseManager (загружает 24 категории фраз из JSON)
phrase_manager = PhraseManager()


def _parse_decoration_upgrades(data):
    """
    ✅ Универсальная функция для парсинга decoration_upgrades.
    Работает и со строкой (JSON), и с dict.
    """
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except:
            return {}
    return {}


def _get_castle_access_level(user_data: dict) -> str:
    """
    Определяет уровень доступа к замку.
    
    Returns:
        str: "locked" | "preview" | "full"
    """
    defeated_bosses = user_data.get("defeated_bosses", [])
    completed_normal = user_data.get("completed_normal_game", False)
    player_level = user_data.get("level", 1)
    
    if "final_boss" in defeated_bosses or completed_normal:
        return "full"  # ✅ Полная победа
    elif player_level >= 5:
        return "preview"  # 🏰 Тизер с 5 уровня
    else:
        return "locked"  # 🔒 Закрыт до 5 уровня


async def trigger_vladimir_first_meeting(user_id: str, context, storage):
    """
    🎬 Кат-сцена первой встречи с Владимиром.
    Запускается только один раз после победы над Финальным Владыком.
    ✅ Все mood заменены на "calm" пока нет других аватарок
    """
    adapter = context.bot_data.get('adapter')
    if not adapter:
        logger.warning(f"⚠️ Adapter not found for trigger_vladimir_first_meeting")
        return
    
    import asyncio
    from pathlib import Path
    from telegram import InputFile, ReplyKeyboardMarkup, KeyboardButton
    
    logger.info(f"🎬 Запуск кат-сцены Владимира для user_id={user_id}")
    
    # === КАТ-СЦЕНА: ПОЯВЛЕНИЕ ===
    
    # 1. Аватарка (без текста, для эффекта)
    avatar_path = Path("images") / "vladimir_calm.jpg"
    if avatar_path.exists():
        try:
            await adapter.bot.send_photo(
                chat_id=user_id,
                photo=InputFile(str(avatar_path)),
                caption=""
            )
            logger.info(f"✅ Отправлена аватарка Владимира (calm) для кат-сцены")
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить аватарку Владимира: {e}")
    else:
        logger.warning(f"⚠️ Файл аватарки не найден: {avatar_path}")
    
    # 2. Реплики с паузами (все mood="calm")
    phrases = [
        "🎩 «Ах... Вы и есть та самая... Морковка?»",
        "🎩 «Я слышал, Вы победили Владыку. Впечатляюще. Особенно для того, кто считал, что 7×8=54.»",
        "🎩 «Добро пожаловать в Ваш Замок, сударыня. Я — Владимир, Ваш дворецкий.»",
        "🎩 «Чай?.. Разумеется. Хотя, судя по Вашим последним решениям, Вам больше подойдёт кофе... с двойной порцией сахара для мозгов.»",
    ]
    
    for phrase in phrases:
        await send_character_message_by_id(user_id, phrase, "vladimir", "calm", context)
        await asyncio.sleep(0.7)
    
    # 3. Открываем ПОЛНОЕ меню замка
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🎨 Декорации"), KeyboardButton("🗝️ Тайная Комната")],
            [KeyboardButton("📊 Зал Славы"), KeyboardButton("🍵 Поболтать")],
            [KeyboardButton("💰 Оплатить upkeep"), KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    
    await adapter.send_message(
        user_id=user_id,
        text="🏰 <b>ЗАМОК ЧИСЛЯНДИИ</b>\n\n«Ваш дом, сударыня. Распоряжайтесь.»",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    logger.info(f"✅ Кат-сцена Владимира завершена для user_id={user_id}")


async def show_castle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать состояние Замка — с гибридным доступом + Владимир"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер платформы не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    user_data = storage.get_user(user_id)
    access_level = _get_castle_access_level(user_data)
    
    logger.info(f"🏰 Замок: user_id={user_id}, access={access_level}, level={user_data.get('level', 1)}")
    
    # === 🔒 ЗАМОК ЗАКРЫТ (до 5 уровня) ===
    if access_level == "locked":
        phrase = phrase_manager.get_vladimir_phrase("castle_locked")
        logger.info(f"🎩 Отправка сообщения Владимира (locked): {phrase[:50]}...")
        await send_character_message(update, context, "vladimir", phrase, mood="calm")
        return
    
    # === 🏰 ЗАМОК ОТКРЫТ — ТИЗЕР (5+ уровень, но нет победы) ===
    if access_level == "preview":
        phrase = phrase_manager.get_vladimir_phrase("castle_preview")
        logger.info(f"🎩 Отправка сообщения Владимира (preview): {phrase[:50]}...")
        await send_character_message(update, context, "vladimir", phrase, mood="calm")
        
        keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("🏰 Осмотреть зал")],
                [KeyboardButton("🍵 Поболтать с Владимиром")],
                [KeyboardButton("🔒 Декорации (после победы)")],
                [KeyboardButton("⬅️ Назад")],
            ],
            resize_keyboard=True
        )
        
        msg = "🏰 <b>ЗАМОК ЧИСЛЯНДИИ</b>\n\n"
        msg += "«Замок открыт, сударыня. Но настоящие сокровища ждут после победы.»\n\n"
        msg += "🔒 <i>Декорации станут доступны после победы над Финальным Владыкой.</i>"
        
        await adapter.send_message(
            user_id=user_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # === 👑 ЗАМОК ПОЛНОСТЬЮ ОТКРЫТ (победа над Владыкой) ===
    phrase = phrase_manager.get_vladimir_phrase("castle_full")
    logger.info(f"🎩 Отправка сообщения Владимира (full): {phrase[:50]}...")
    await send_character_message(update, context, "vladimir", phrase, mood="calm")
    
    # ✅ Получаем информацию о замке из CastleEngine
    engine = context.bot_data.get('engine')
    if engine:
        castle_info = engine.get_castle_info(user_id)
    else:
        castle_info = {"error": "Ядро не инициализировано"}
    
    # ✅ Формируем сообщение
    msg = "🏰 <b>ЗАМОК ЧИСЛЯНДИИ</b>\n\n"
    
    # Upkeep статус
    if castle_info.get("bonuses_active", False):
        days = castle_info.get("days_remaining", 0)
        msg += f"✅ <b>Upkeep оплачен</b> на {days} дн.\n"
        msg += f"🎁 <b>Бонусы активны:</b> {castle_info.get('total_bonus_display', '+0%')}\n\n"
    else:
        upkeep_phrase = phrase_manager.get_vladimir_phrase("upkeep_reminder")
        msg += f"🎩 <i>{upkeep_phrase}</i>\n"
        msg += "❌ <b>Upkeep НЕ оплачен!</b>\n"
        msg += "💡 Оплати: 💰 Оплатить upkeep\n\n"
    
    # ✅ Декорации с уровнями
    msg += "🎨 <b>Декорации:</b>\n"
    
    # ✅ ПАРСИМ decoration_upgrades ИЗ JSON СТРОКИ!
    decoration_upgrades = _parse_decoration_upgrades(castle_info.get("decoration_upgrades", {}))
    
    if decoration_upgrades:
        has_any = False
        for dec in CASTLE_DECORATIONS:
            level = decoration_upgrades.get(dec["id"], 0)
            if level > 0:
                has_any = True
                bonus = dec["bonus_per_level"] + (dec["bonus_per_level"] * (level - 1))
                bonus = min(bonus, dec["max_bonus"])
                msg += f"   {dec.get('emoji', '🏰')} {dec['name']} — <b>ур. {level}</b> (+{int(bonus * 100)}%)\n"
        
        if not has_any:
            no_dec_phrase = phrase_manager.get_vladimir_phrase("no_decorations") if "no_decorations" in phrase_manager.vladimir_phrases else "📭 Пока нет декораций. Купите в 🎨 Декорации"
            msg += f"   {no_dec_phrase}\n"
    else:
        no_dec_phrase = phrase_manager.get_vladimir_phrase("no_decorations") if "no_decorations" in phrase_manager.vladimir_phrases else "📭 Пока нет декораций. Купите в 🎨 Декорации"
        msg += f"   {no_dec_phrase}\n"
    
    msg += "\n💡 <i>Улучшай декорации для увеличения бонусов!</i>"
    
    # ✅ Клавиатура — КНОПКА "🗝️ Тайная Комната" ОСТАЁТСЯ
    # Но хендлер для неё НЕ регистрируется здесь — обработка в secret_room.py
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🎨 Декорации"), KeyboardButton("💰 Оплатить upkeep")],
            [KeyboardButton("🗝️ Тайная Комната"), KeyboardButton("🍵 Поболтать с Владимиром")],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def show_castle_decorations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать декорации для покупки/улучшения — С УРОВНЯМИ"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    user_data = storage.get_user(user_id)
    access_level = _get_castle_access_level(user_data)
    
    # ✅ Проверка доступа (только full)
    if access_level != "full":
        phrase = phrase_manager.get_vladimir_phrase("castle_locked")
        await send_character_message(update, context, "vladimir", phrase, mood="calm")
        return
    
    balance = user_data.get("score_balance", 0)
    
    # ✅ ПАРСИМ decoration_upgrades ИЗ JSON СТРОКИ!
    decoration_upgrades = _parse_decoration_upgrades(user_data.get("decoration_upgrades", {}))
    
    msg = "🎨 <b>ДЕКОРАЦИИ ЗАМКА</b>\n\n"
    msg += f"💰 <b>Баланс:</b> {balance:,} золотых\n\n"
    msg += "Нажми на декорацию для покупки или улучшения!\n"
    msg += "Цена растёт с каждым уровнем.\n\n"
    
    for dec in CASTLE_DECORATIONS:
        current_level = decoration_upgrades.get(dec["id"], 0)
        
        # Рассчитываем цену следующего уровня
        if current_level == 0:
            price = dec.get("base_price", 300)
            level_text = "❌ Не куплен"
        else:
            # Формула: base_price × multiplier^level
            price = int(dec.get("base_price", 300) * (dec.get("cost_multiplier", 1.4) ** current_level))
            level_text = f"✅ Уровень {current_level}"
        
        can_buy = "✅" if balance >= price else "❌"
        
        # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ БОНУСА
        bonus_per_level = dec.get("bonus_per_level", 0.02)
        max_bonus = dec.get("max_bonus", 0.10)
        bonus = bonus_per_level + (bonus_per_level * current_level) if current_level > 0 else bonus_per_level
        bonus = min(bonus, max_bonus)
        
        msg += f"{can_buy} {dec.get('emoji', '🏰')} {dec['name']}\n"
        msg += f"   {level_text} | 💰 {price:,} золотых | 🎁 +{int(bonus * 100)}%\n"
        msg += f"   _{dec.get('description', '')}_\n\n"
    
    # Фраза от Владимира
    greeting_phrase = phrase_manager.get_vladimir_phrase("greeting")
    msg += f"🎩 <i>{greeting_phrase}</i>"
    
    rows = [[KeyboardButton(dec["name"])] for dec in CASTLE_DECORATIONS]
    rows.append(["⬅️ Назад"])
    
    keyboard = ReplyKeyboardMarkup(rows, resize_keyboard=True)
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def upgrade_decoration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка покупки/улучшения декорации"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    item_name = update.message.text.strip()
    
    # Ищем декорацию по имени
    dec_config = None
    for dec in CASTLE_DECORATIONS:
        if dec["name"] == item_name:
            dec_config = dec
            break
    
    if not dec_config:
        await adapter.send_message(user_id, "❌ Декорация не найдена!")
        return
    
    engine = context.bot_data.get('engine')
    if not engine:
        await adapter.send_message(user_id, "❌ Ошибка: ядро не инициализировано!")
        return
    
    # Вызываем upgrade_decoration из CastleEngine
    success, message = engine.castle.upgrade_decoration(user_id, dec_config["id"])
    
    if not success:
        await adapter.send_message(user_id, message)
        return
    
    # ✅ Успех — показываем сообщение от Владимира
    phrase = phrase_manager.get_vladimir_phrase("upgrade_decoration")
    logger.info(f"🎩 Отправка сообщения Владимира (upgrade): {phrase[:50]}...")
    await send_character_message(update, context, "vladimir", f"{phrase}\n\n{message}", mood="calm")
    
    log_user_action(user_id, "DECORATION_UPGRADED", f"decoration={dec_config['id']}")


async def talk_to_vladimir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просто поболтать с Владимиром"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    phrase = phrase_manager.get_vladimir_phrase("idle_chat")
    logger.info(f"🎩 Отправка сообщения Владимира (idle_chat): {phrase[:50]}...")
    await send_character_message(update, context, "vladimir", phrase, mood="calm")


async def pay_upkeep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплатить upkeep Замка"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано.")
        return
    
    days = 1
    if context.args and context.args[0].isdigit():
        days = int(context.args[0])
        if days > 30:
            await adapter.send_message(user_id, "❌ Максимум 30 дней за раз!")
            return
    
    result = engine.castle.pay_upkeep(user_id, days)
    
    # ✅ Добавляем фразу Владимира
    if result[0]:  # Успех
        phrase = phrase_manager.get_vladimir_phrase("upkeep_paid")
        logger.info(f"🎩 Отправка сообщения Владимира (upkeep_paid): {phrase[:50]}...")
        await send_character_message(update, context, "vladimir", f"{phrase}\n\n{result[1]}", mood="calm")
    else:  # Ошибка
        phrase = phrase_manager.get_vladimir_phrase("upkeep_reminder")
        logger.info(f"🎩 Отправка сообщения Владимира (upkeep_reminder): {phrase[:50]}...")
        await send_character_message(update, context, "vladimir", f"{phrase}\n\n{result[1]}", mood="calm")


async def castle_pay_1_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    if engine:
        result = engine.castle.pay_upkeep(user_id, 1)
        if result[0]:
            phrase = phrase_manager.get_vladimir_phrase("upkeep_paid")
            await send_character_message(update, context, "vladimir", f"{phrase}\n\n{result[1]}", mood="calm")
        else:
            await adapter.send_message(user_id, result[1])


async def castle_pay_7_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    if engine:
        result = engine.castle.pay_upkeep(user_id, 7)
        if result[0]:
            phrase = phrase_manager.get_vladimir_phrase("upkeep_paid")
            await send_character_message(update, context, "vladimir", f"{phrase}\n\n{result[1]}", mood="calm")
        else:
            await adapter.send_message(user_id, result[1])


async def castle_pay_30_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    if engine:
        result = engine.castle.pay_upkeep(user_id, 30)
        if result[0]:
            phrase = phrase_manager.get_vladimir_phrase("upkeep_paid")
            await send_character_message(update, context, "vladimir", f"{phrase}\n\n{result[1]}", mood="calm")
        else:
            await adapter.send_message(user_id, result[1])


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    from core.ui_helpers import get_persistent_keyboard
    keyboard = get_persistent_keyboard(user_data, menu="main")
    
    # Прощание от Владимира
    phrase = phrase_manager.get_vladimir_phrase("farewell")
    logger.info(f"🎩 Отправка сообщения Владимира (farewell): {phrase[:50]}...")
    await send_character_message(update, context, "vladimir", phrase, mood="calm")
    
    await adapter.send_message(
        user_id=user_id,
        text="🏰 *ГЛАВНОЕ МЕНЮ*\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


def get_castle_handlers():
    """Возвращает список хендлеров замка"""
    return [
        CommandHandler("castle", show_castle),
        CommandHandler("pay_upkeep", pay_upkeep),
        
        # Кнопки upkeep
        MessageHandler(filters.Text("💰 Оплатить 1 день") & ~filters.COMMAND, castle_pay_1_day),
        MessageHandler(filters.Text("💰 Оплатить 7 дней") & ~filters.COMMAND, castle_pay_7_days),
        MessageHandler(filters.Text("💰 Оплатить 30 дней") & ~filters.COMMAND, castle_pay_30_days),
        MessageHandler(filters.Text("💰 Оплатить upkeep") & ~filters.COMMAND, castle_pay_1_day),
        
        # Кнопки декораций
        MessageHandler(filters.Text("🎨 Декорации") & ~filters.COMMAND, show_castle_decorations),
        MessageHandler(filters.Text("🎨 Купить декорацию") & ~filters.COMMAND, show_castle_decorations),
        
        # Кнопки конкретных декораций
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & 
            (filters.Text("🥕 Морковки на стене") | filters.Text("🕯️ Серебряные подсвечники") |
             filters.Text("🖼️ Портрет Пифагора") | filters.Text("📐 Обои «Сад формул»") |
             filters.Text("💡 Хрустальная люстра") | filters.Text("🪑 Трон из учебников") |
             filters.Text("🌟 Звёздный купол") | filters.Text("🎩 Монокль Владимира")),
            upgrade_decoration
        ),
        
        # Поболтать с Владимиром
        MessageHandler(filters.Text("🍵 Поболтать с Владимиром") & ~filters.COMMAND, talk_to_vladimir),
        MessageHandler(filters.Text("🍵 Поболтать") & ~filters.COMMAND, talk_to_vladimir),
        MessageHandler(filters.Text("🏰 Осмотреть зал") & ~filters.COMMAND, show_castle),
        
        # Навигация
        MessageHandler(filters.Text("⬅️ Назад") & ~filters.COMMAND, back_to_menu),
        
        # ✅ КНОПКА "🗝️ Тайная Комната" НЕ РЕГИСТРИРУЕТСЯ ЗДЕСЬ
        # Она есть в клавиатуре (show_castle), но обработчик только в secret_room.py
        # Это позволяет кнопке "проваливаться" к правильному хендлеру
    ]