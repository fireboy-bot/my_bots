# handlers/bank.py
"""
Хендлеры Златочёта — команды /bank, /deposit, /withdraw + КНОПКИ
Версия: 2.0 (Кнопочный интерфейс для Морковки) 🏦🎮
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler

async def show_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать состояние Златочёта с кнопками"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    bank_data = engine.get_bank_info(user_id)
    
    msg = "🏦 <b>ЗЛАТОЧЁТ — ХРАНИЛИЩЕ ЧИСЕЛ</b>\n\n"
    msg += f"💰 <b>Ваш вклад:</b> {bank_data['balance']} золотых\n"
    msg += f"📈 <b>Накоплено процентов:</b> {bank_data['interest_earned']} золотых\n"
    msg += f"⏰ <b>Дней в банке:</b> {bank_data['days_passed']}\n\n"
    msg += "💡 <b>Ставка Казнодея:</b> 10% в день\n"
    msg += "💡 <b>Мин. вклад:</b> 100 золотых\n\n"
    msg += "🎩 <i>«Златочёт надёжно хранит Ваши сокровища!» — Владимир</i>"
    
    # ✅ КНОПКИ БАНКА
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("💰 Положить 100"), KeyboardButton("💰 Положить 500")],
            [KeyboardButton("💰 Положить 1000"), KeyboardButton("💰 Другая сумма")],
            [KeyboardButton("💸 Забрать всё"), KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=keyboard)

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить золотые в Златочёт (через команду)"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Используйте: /deposit <сумма>\nПример: /deposit 500")
        return
    
    amount = int(context.args[0])
    result = engine.deposit_to_bank(user_id, amount)
    
    await update.message.reply_text(result['message'])

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забрать вклад с процентами"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.withdraw_from_bank(user_id)
    
    # После снятия — возвращаем обычное меню
    from core.ui_helpers import get_persistent_keyboard
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    await update.message.reply_text(
        result['message'],
        reply_markup=get_persistent_keyboard(user_data)
    )

# ============================================
# ✅ НОВЫЕ ФУНКЦИИ ДЛЯ КНОПОК
# ============================================

async def bank_deposit_100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить 100 золотых"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.deposit_to_bank(user_id, 100)
    await update.message.reply_text(result['message'])

async def bank_deposit_500(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить 500 золотых"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.deposit_to_bank(user_id, 500)
    await update.message.reply_text(result['message'])

async def bank_deposit_1000(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить 1000 золотых"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.deposit_to_bank(user_id, 1000)
    await update.message.reply_text(result['message'])

async def bank_deposit_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить другую сумму (запрос числа)"""
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3")],
            [KeyboardButton("4"), KeyboardButton("5"), KeyboardButton("6")],
            [KeyboardButton("7"), KeyboardButton("8"), KeyboardButton("9")],
            [KeyboardButton("⬅️ Назад"), KeyboardButton("0"), KeyboardButton("✅ Готово")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "💰 <b>Введите сумму для вклада:</b>\n\n"
        "Минимум: 100 золотых\n"
        "Нажмите цифры по очереди, затем «✅ Готово»",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    # Устанавливаем состояние ожидания ввода
    context.user_data['bank_deposit_mode'] = True
    context.user_data['bank_deposit_amount'] = ''

async def bank_withdraw_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забрать весь вклад"""
    await withdraw(update, context)

# ============================================
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# ============================================

def get_bank_handlers():
    """Возвращает список хендлеров банка"""
    return [
        CommandHandler("bank", show_bank),
        CommandHandler("deposit", deposit),
        CommandHandler("withdraw", withdraw),
    ]