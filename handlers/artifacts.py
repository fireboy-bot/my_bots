# handlers/artifacts.py
"""
Хендлеры артефактов — команды /artifacts и /upgrade.
Версия: 1.0 (MVP) 🔮
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from core.logger import log_user_action
from core.ui_helpers import get_persistent_keyboard
from items import ARTIFACTS

logger = logging.getLogger(__name__)


async def show_artifacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все артефакты игрока"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    logger.info(f"🔮 show_artifacts вызван для user_id={user_id}")
    
    engine = context.bot_data.get('engine')
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано.")
        return
    
    # Получаем информацию об артефактах
    artifacts = engine.get_artifact_info(user_id)
    
    # Проверяем upkeep
    castle_info = engine.get_castle_info(user_id)
    upkeep_active = castle_info.get("bonuses_active", False)
    
    msg = "🔮 <b>ВАШИ АРТЕФАКТЫ</b>\n\n"
    
    if not upkeep_active:
        msg += "⚠️ <b>Upkeep замка не оплачен!</b>\n"
        msg += "Артефакты не работают, пока не оплатите содержание.\n\n"
    
    for artifact_id, data in artifacts.items():
        icon = "🍀" if "luck" in artifact_id else "⚡" if "power" in artifact_id else "🧠"
        status = "✅" if data["level"] > 0 else "⬜"
        
        # Если upkeep не оплачен — показываем неактивным
        if not upkeep_active and data.get("requires_upkeep", True):
            active_status = "❌ НЕ АКТИВЕН"
        else:
            active_status = "✅ АКТИВЕН" if data["level"] > 0 else "⬜ НЕ КУПЛЕН"
        
        msg += f"{status} <b>{data['name']}</b>\n"
        msg += f"   Уровень: {data['level']}/{data['max_level']}\n"
        msg += f"   Эффект: {data['effect']}\n"
        msg += f"   Статус: {active_status}\n"
        
        if data["next_upgrade_cost"]:
            msg += f"   💰 Улучшение: {data['next_upgrade_cost']:,} золотых\n"
        else:
            msg += f"   ⚡ <b>МАКСИМАЛЬНЫЙ УРОВЕНЬ!</b>\n"
        
        msg += "\n"
    
    msg += "💡 <i>Для улучшения:</i> `/upgrade [артефакт]`\n"
    msg += "Пример: `/upgrade artifact_luck`"
    
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🍀 Улучшить Удачу"), KeyboardButton("⚡ Улучшить Силу")],
            [KeyboardButton("🧠 Улучшить Мудрость"), KeyboardButton("⬅️ Назад")],
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


async def upgrade_artifact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Улучшить артефакт по команде"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    if not context.args:
        await adapter.send_message(
            user_id,
            "💡 <b>Использование:</b> `/upgrade [артефакт]`\n\n"
            "Примеры:\n"
            "`/upgrade artifact_luck`\n"
            "`/upgrade artifact_power`\n"
            "`/upgrade artifact_wisdom`",
            parse_mode="HTML"
        )
        return
    
    artifact_id = context.args[0]
    
    # Проверяем, существует ли артефакт
    if artifact_id not in ARTIFACTS:
        await adapter.send_message(user_id, f"❌ Артефакт <b>{artifact_id}</b> не найден!", parse_mode="HTML")
        return
    
    engine = context.bot_data.get('engine')
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано.")
        return
    
    # Улучшаем артефакт
    success, message = engine.upgrade_artifact(user_id, artifact_id)
    
    await adapter.send_message(user_id, message)
    
    if success:
        log_user_action(user_id, "ARTIFACT_UPGRADED", f"artifact={artifact_id}")


async def upgrade_artifact_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок улучшения артефактов"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    text = update.message.text.strip()
    
    # Маппинг кнопок на artifact_id
    button_map = {
        "🍀 Улучшить Удачу": "artifact_luck",
        "⚡ Улучшить Силу": "artifact_power",
        "🧠 Улучшить Мудрость": "artifact_wisdom"
    }
    
    artifact_id = button_map.get(text)
    if not artifact_id:
        return  # Не наша кнопка
    
    engine = context.bot_data.get('engine')
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано.")
        return
    
    success, message = engine.upgrade_artifact(user_id, artifact_id)
    await adapter.send_message(user_id, message)
    
    if success:
        log_user_action(user_id, "ARTIFACT_UPGRADED_BUTTON", f"artifact={artifact_id}")
        
        # Показываем обновлённый список артефактов
        await asyncio.sleep(1)
        await show_artifacts(update, context)


async def buy_artifact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка первого артефакта (через магазин)"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id)
    balance = user_data.get("score_balance", 0)
    
    # Временная логика: покупка = улучшение с уровня 0 до 1
    engine = context.bot_data.get('engine')
    if not engine:
        await adapter.send_message(user_id, "⚠️ Ошибка: ядро не инициализировано.")
        return
    
    # Определяем артефакт по названию (из магазина)
    artifact_map = {
        "🍀 Артефакт Удачи": "artifact_luck",
        "⚡ Артефакт Силы": "artifact_power",
        "🧠 Артефакт Мудрости": "artifact_wisdom"
    }
    
    # Это будет обрабатываться через buy_item в shop.py
    # Здесь просто заглушка для будущего расширения
    await adapter.send_message(
        user_id,
        "💡 Артефакты покупаются через `/upgrade` после первого приобретения.\n"
        "Первое улучшение = покупка артефакта."
    )


def get_artifact_handlers():
    """Возвращает список хендлеров артефактов"""
    return [
        CommandHandler("artifacts", show_artifacts),
        CommandHandler("upgrade", upgrade_artifact),
        MessageHandler(
            filters.Text("🍀 Улучшить Удачу") & ~filters.COMMAND,
            upgrade_artifact_button
        ),
        MessageHandler(
            filters.Text("⚡ Улучшить Силу") & ~filters.COMMAND,
            upgrade_artifact_button
        ),
        MessageHandler(
            filters.Text("🧠 Улучшить Мудрость") & ~filters.COMMAND,
            upgrade_artifact_button
        ),
    ]