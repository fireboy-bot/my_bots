# handlers/castle.py
"""
Хендлеры Замка — команды /castle, /pay_upkeep + КНОПКИ
Версия: 2.0 (Кнопочный интерфейс для Морковки) 🏰🎮
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler

async def show_castle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать состояние Замка с кнопками"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    castle_info = engine.castle.get_castle_state(user_id)
    
    msg = "🏰 <b>ЗАМОК ЧИСЛЯНДИИ</b>\n\n"
    
    # Декорации
    decorations = castle_info.get("decorations", [])
    if decorations:
        msg += "🎨 <b>Декорации:</b>\n"
        for dec in decorations[:10]:
            name = dec.get('name', 'Неизвестно')
            msg += f"  ▫️ {name}\n"
        if len(decorations) > 10:
            msg += f"  ... и ещё {len(decorations) - 10}\n"
    else:
        msg += "🎨 <b>Декорации:</b> пока нет\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Upkeep
    total_upkeep = castle_info.get("total_upkeep", 0)
    days_left = castle_info.get("days_left", 0)
    bonuses_active = castle_info.get("bonuses_active", False)
    bonus_percent = castle_info.get("bonus_percent", 0)
    
    msg += f"💰 <b>Ежедневный upkeep:</b> {total_upkeep} золотых\n"
    
    if bonuses_active:
        msg += f"✅ <b>Upkeep оплачен на {days_left} дн.</b>\n"
        msg += f"🌟 <b>Бонус к очкам:</b> +{bonus_percent}%\n"
    else:
        msg += "❌ <b>Upkeep не оплачен!</b>\n"
        msg += "⚠️ Бонусы не активны\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🎩 <i>«Ваш Замок — символ Вашего прогресса!» — Владимир</i>"
    
    # ✅ КНОПКИ ЗАМКА
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("💰 Оплатить 1 день"), KeyboardButton("💰 Оплатить 7 дней")],
            [KeyboardButton("💰 Оплатить 30 дней"), KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=keyboard)

async def pay_upkeep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплатить upkeep Замка (через команду)"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    days = 1
    if context.args and context.args[0].isdigit():
        days = int(context.args[0])
        if days > 30:
            await update.message.reply_text("❌ Максимум 30 дней за раз!")
            return
    
    result = engine.castle.pay_upkeep(user_id, days)
    await update.message.reply_text(result[1])

# ============================================
# ✅ НОВЫЕ ФУНКЦИИ ДЛЯ КНОПОК
# ============================================

async def castle_pay_1_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплатить 1 день"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.castle.pay_upkeep(user_id, 1)
    await update.message.reply_text(result[1])

async def castle_pay_7_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплатить 7 дней"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.castle.pay_upkeep(user_id, 7)
    await update.message.reply_text(result[1])

async def castle_pay_30_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплатить 30 дней"""
    user_id = update.effective_user.id
    engine = context.bot_data.get('engine')
    
    if not engine:
        await update.message.reply_text("⚠️ Ошибка: ядро не инициализировано")
        return
    
    result = engine.castle.pay_upkeep(user_id, 30)
    await update.message.reply_text(result[1])

# ============================================
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# ============================================

def get_castle_handlers():
    """Возвращает список хендлеров Замка"""
    return [
        CommandHandler("castle", show_castle),
        CommandHandler("pay_upkeep", pay_upkeep),
    ]