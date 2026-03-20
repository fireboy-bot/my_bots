# handlers/bank.py
"""
Хендлеры Златочёта — команды /bank, /deposit, /withdraw + КНОПКИ
Версия: 3.1 (Fix: send_character_message signature + Gold Currency) 🏦🎩💰✅
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from core.logger import log_user_action
from core.ui_helpers import get_persistent_keyboard
from handlers.narrative_manager import PhraseManager, send_character_message

logger = logging.getLogger(__name__)
phrase_manager = PhraseManager()


async def show_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать состояние Златочёта — ЧЁТКОЕ РАЗДЕЛЕНИЕ!"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано")
        return
    
    bank_data = engine.get_bank_info(user_id)
    
    # ✅ ЧЁТКИЕ ПЕРЕМЕННЫЕ — НЕ ПУТАТЬ!
    balance_on_hand = bank_data.get("balance", 0)  # Золото НА РУКАХ
    bank_balance = bank_data.get("bank_balance", 0)  # Вклад В БАНКЕ
    interest_earned = bank_data.get("interest_earned", 0)  # Проценты
    interest_rate = bank_data.get("bank_interest", 0.10)
    days_passed = bank_data.get("days_passed", 0)
    
    total_withdraw = bank_balance + interest_earned  # Сколько можно забрать
    
    msg = "🏦 <b>ЗЛАТОЧЁТ — ХРАНИЛИЩЕ ЧИСЕЛ</b>\n\n"
    msg += f"💰 <b>На руках:</b> {balance_on_hand:,} золотых\n"
    msg += f"🏦 <b>Вклад в банке:</b> {bank_balance:,} золотых\n"
    msg += f"📈 <b>Накоплено процентов:</b> {interest_earned:,} золотых\n"
    msg += f"⏰ <b>Дней в банке:</b> {days_passed}\n"
    msg += f"💵 <b>Можно забрать:</b> {total_withdraw:,} золотых\n\n"
    msg += "💡 <b>Ставка Казнодея:</b> " + str(int(interest_rate * 100)) + "% в день\n"
    msg += "💡 <b>Мин. вклад:</b> 100 золотых\n\n"
    msg += "🎩 <i>«Златочёт надёжно хранит Ваши сокровища!» — Владимир</i>"
    
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("💰 Положить 100"), KeyboardButton("💰 Положить 500")],
            [KeyboardButton("💰 Положить 1000"), KeyboardButton("💰 Другая сумма")],
            [KeyboardButton("💸 Забрать всё"), KeyboardButton("⬅️ Назад")],
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


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить золотые в Златочёт (через команду)"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано")
        return
    
    if not context.args or not context.args[0].isdigit():
        await adapter.send_message(
            user_id,
            "❌ Используйте: /deposit <сумма>\nПример: /deposit 500"
        )
        return
    
    amount = int(context.args[0])
    result = engine.deposit_to_bank(user_id, amount)
    
    success, message = _parse_result(result)
    
    # ✅ Комментарий Владимира если замок открыт
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    if phrase_manager.is_castle_unlocked(user_data) and success:
        phrase = phrase_manager.get_vladimir_phrase("bank_deposit")
        await send_character_message(
            update, context, "vladimir",  # ← context добавлен!
            f"{phrase}\n\n{message}",
            mood="approve"
        )
    else:
        await adapter.send_message(user_id, message)


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забрать вклад с процентами"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.withdraw_from_bank(user_id)
    
    success, message = _parse_result(result)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    keyboard = get_persistent_keyboard(user_data)
    
    # ✅ Комментарий Владимира если замок открыт
    if phrase_manager.is_castle_unlocked(user_data) and success:
        phrase = phrase_manager.get_vladimir_phrase("bank_withdraw")
        await send_character_message(
            update, context, "vladimir",  # ← context добавлен!
            f"{phrase}\n\n{message}",
            mood="calm"
        )
    else:
        await adapter.send_message(
            user_id=user_id,
            text=message,
            reply_markup=keyboard
        )


# ============================================
# ✅ ФУНКЦИИ ДЛЯ КНОПОК
# ============================================

async def bank_deposit_100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить 100 золотых"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.deposit_to_bank(user_id, 100)
    success, message = _parse_result(result)
    
    # ✅ Комментарий Владимира если замок открыт
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    if phrase_manager.is_castle_unlocked(user_data) and success:
        phrase = phrase_manager.get_vladimir_phrase("bank_deposit")
        await send_character_message(
            update, context, "vladimir",  # ← context добавлен!
            f"{phrase}\n\n{message}",
            mood="approve"
        )
    else:
        await adapter.send_message(user_id, message)


async def bank_deposit_500(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить 500 золотых"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.deposit_to_bank(user_id, 500)
    success, message = _parse_result(result)
    
    # ✅ Комментарий Владимира если замок открыт
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    if phrase_manager.is_castle_unlocked(user_data) and success:
        phrase = phrase_manager.get_vladimir_phrase("bank_deposit")
        await send_character_message(
            update, context, "vladimir",  # ← context добавлен!
            f"{phrase}\n\n{message}",
            mood="approve"
        )
    else:
        await adapter.send_message(user_id, message)


async def bank_deposit_1000(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить 1000 золотых"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    engine = context.bot_data.get('engine')
    
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.deposit_to_bank(user_id, 1000)
    success, message = _parse_result(result)
    
    # ✅ Комментарий Владимира если замок открыт
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    if phrase_manager.is_castle_unlocked(user_data) and success:
        phrase = phrase_manager.get_vladimir_phrase("bank_deposit")
        await send_character_message(
            update, context, "vladimir",  # ← context добавлен!
            f"{phrase}\n\n{message}",
            mood="approve"
        )
    else:
        await adapter.send_message(user_id, message)


async def bank_deposit_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить другую сумму (через /deposit)"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    await adapter.send_message(
        user_id=user_id,
        text=(
            "💰 <b>Введите сумму для вклада:</b>\n\n"
            "Используйте команду: <code>/deposit 500</code>\n\n"
            "Минимум: 100 золотых"
        ),
        parse_mode="HTML"
    )


async def bank_withdraw_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забрать весь вклад"""
    await withdraw(update, context)


def _parse_result(result):
    """
    Универсальная функция для парсинга результатов от engine.
    ✅ Работает и с tuple, и с dict
    """
    if isinstance(result, tuple):
        success = result[0] if len(result) > 0 else False
        message = result[1] if len(result) > 1 else "✅ Операция выполнена"
        return success, message
    elif isinstance(result, dict):
        return result.get('success', True), result.get('message', '✅ Операция выполнена')
    else:
        return False, "⚠️ Неизвестный формат результата"


# ============================================
# ✅ РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# ============================================

def get_bank_handlers():
    """Возвращает список хендлеров банка"""
    return [
        CommandHandler("bank", show_bank),
        CommandHandler("deposit", deposit),
        CommandHandler("withdraw", withdraw),
        
        # ✅ КНОПКИ ВКЛАДОВ
        MessageHandler(
            filters.Text("💰 Положить 100") & ~filters.COMMAND,
            bank_deposit_100
        ),
        MessageHandler(
            filters.Text("💰 Положить 500") & ~filters.COMMAND,
            bank_deposit_500
        ),
        MessageHandler(
            filters.Text("💰 Положить 1000") & ~filters.COMMAND,
            bank_deposit_1000
        ),
        MessageHandler(
            filters.Text("💰 Другая сумма") & ~filters.COMMAND,
            bank_deposit_custom
        ),
        MessageHandler(
            filters.Text("💸 Забрать всё") & ~filters.COMMAND,
            bank_withdraw_all
        ),
    ]