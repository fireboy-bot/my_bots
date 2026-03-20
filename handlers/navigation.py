# handlers/navigation.py
"""
Глобальная навигация — PRO версия (ТОЧЕЧНЫЙ ПЕРЕХВАТ)
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, ApplicationHandlerStop
from core.ui_helpers import get_persistent_keyboard
from core.logger import log_user_action

logger = logging.getLogger(__name__)


# ✅ ЧЁТКИЙ список навигационных команд
NAVIGATION_TEXTS = [
    "⬅️ Назад",
    "⬅️",
    "назад",
    "Назад",
    "выйти",
    "выход",
    "меню",
    "главное меню",
]


async def handle_global_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ТОЛЬКО навигационные кнопки"""

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id if update.effective_user else 0
    first_name = update.effective_user.first_name if update.effective_user else "Игрок"

    logger.info(f"🧭 GLOBAL NAVIGATION: '{text}' от user_id={user_id}")
    log_user_action(user_id, "NAVIGATION", f"text='{text}'")

    storage = context.bot_data.get("storage")
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        raise ApplicationHandlerStop

    user_data = storage.get_user(user_id) or {}
    exited_from = []

    # === ВЫХОД ИЗ УРОВНЯ ===
    if user_data.get("current_level"):
        user_data.update({
            "current_level": None,
            "selected_tasks": [],
            "current_task_index": 0,
            "mistakes_in_level": 0
        })
        exited_from.append("уровня")

    # === ВЫХОД ИЗ БОЯ ===
    if user_data.get("in_boss_battle"):
        user_data.update({
            "in_boss_battle": False,
            "current_boss": None,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "boss_health": 5,
            "boss_abilities_used": [],
            "boss_turn": 0
        })
        exited_from.append("боя")

    storage.save_user(user_id, user_data)

    keyboard = get_persistent_keyboard(user_data, menu="main")

    if exited_from:
        exit_message = " и ".join(exited_from)
        await update.message.reply_text(
            f"↩️ Вышла из {exit_message}!\n\nВыберите действие:",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            f"🏰 ГЛАВНОЕ МЕНЮ\n\n{first_name}, выберите действие:",
            reply_markup=keyboard,
        )

    raise ApplicationHandlerStop


def get_navigation_handlers():
    """Регистрируем ТОЛЬКО нужные кнопки"""

    return [
        MessageHandler(filters.Text(text) & ~filters.COMMAND, handle_global_navigation)
        for text in NAVIGATION_TEXTS
    ]

