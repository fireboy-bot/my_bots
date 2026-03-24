# handlers/admin_commands.py
"""
Админ-команды для бота «Числяндия».
Версия: 2.0 (give_balance + Fix) 🗄️💰
"""

import os
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, IS_PRODUCTION
from core.logger import log_audit_action

logger = logging.getLogger(__name__)


async def migrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда миграции (заглушка)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    await update.message.reply_text("✅ Миграция не требуется (SQLite используется по умолчанию).")


async def debug_progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает прогресс пользователя (админ)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    if IS_PRODUCTION:
        await update.message.reply_text("🔒 Команда отключена в production.")
        return
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    progress = storage.get_user(user_id) or {}
    
    text = "📊 **ПРОГРЕСС ПОЛЬЗОВАТЕЛЯ:**\n\n```\n"
    for key, value in list(progress.items())[:20]:
        text += f"{key}: {value}\n"
    text += "```"
    
    if len(str(progress)) > 4000:
        text = text[:4000] + "\n... (обрезано)"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def dump_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полный дамп данных пользователя (админ)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    target_id = int(context.args[0]) if context.args and context.args[0].isdigit() else user_id
    log_audit_action(user_id, "DUMP_USER", f"target={target_id} production={IS_PRODUCTION}")
    
    progress = storage.get_user(target_id) or {}

    if IS_PRODUCTION:
        # Безопасный краткий дамп для продакшна (без полного JSON).
        safe = {
            "user_id": progress.get("user_id", target_id),
            "level": progress.get("level", 1),
            "total_score": progress.get("total_score", 0),
            "score_balance": progress.get("score_balance", 0),
            "tasks_solved": progress.get("tasks_solved", 0),
            "tasks_correct": progress.get("tasks_correct", 0),
            "in_boss_battle": progress.get("in_boss_battle", False),
            "current_level": progress.get("current_level"),
            "current_boss": progress.get("current_boss"),
            "inventory_count": len(progress.get("inventory", [])),
            "rewards_count": len(progress.get("rewards", [])),
        }
        safe_text = json.dumps(safe, indent=2, ensure_ascii=False)
        await update.message.reply_text(
            f"📦 **SAFE DUMP {target_id} (production):**\n```\n{safe_text}\n```",
            parse_mode="Markdown",
        )
        return

    dump_text = json.dumps(progress, indent=2, ensure_ascii=False)
    if len(dump_text) > 4000:
        dump_text = dump_text[:4000] + "\n... (обрезано)"
    await update.message.reply_text(f"📦 **ДАМП ПОЛЬЗОВАТЕЛЯ {target_id}:**\n```\n{dump_text}\n```", parse_mode="Markdown")


async def reset_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбрасывает прогресс пользователя (админ)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    target_id = int(context.args[0]) if context.args and context.args[0].isdigit() else user_id
    log_audit_action(user_id, "RESET_USER", f"target={target_id}")
    storage.delete_user(target_id)
    
    await update.message.reply_text(f"✅ Прогресс пользователя {target_id} сброшен.")


async def give_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдаёт предмет пользователю (админ)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /give user_id item_id")
        return
    
    target = context.args[0]
    item_id = context.args[1]
    
    if target.startswith('@'):
        await update.message.reply_text("⚠️ Поиск по username пока не реализован. Используйте user_id.")
        return
    
    target_id = int(target) if target.isdigit() else user_id
    
    progress = storage.get_user(target_id)
    if not progress:
        await update.message.reply_text(f"❌ Пользователь {target_id} не найден.")
        return
    
    if 'inventory' not in progress:
        progress['inventory'] = []
    
    progress['inventory'].append(item_id)
    storage.save_user(target_id, progress)
    log_audit_action(user_id, "GIVE_ITEM", f"target={target_id} item={item_id}")
    
    await update.message.reply_text(f"✅ Предмет {item_id} выдан пользователю {target_id}.")


# ✅ НОВАЯ КОМАНДА: /give_balance (ПРОСТАЯ И НАДЁЖНАЯ)
async def give_balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить/списать золото пользователю (админ) — ПРОСТАЯ ВЕРСИЯ"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "💰 Использование: `/give_balance [user_id] [сумма]`\n\n"
            "Примеры:\n"
            "`/give_balance 5001966771 1000` — добавить 1000 золота\n"
            "`/give_balance 5001966771 -500` — списать 500 золота",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Ошибка: user_id и сумма должны быть числами!")
        return
    
    # Получаем пользователя
    progress = storage.get_user(target_id)
    if not progress:
        await update.message.reply_text(f"❌ Пользователь {target_id} не найден.")
        return
    
    # Обновляем баланс (просто и надёжно)
    old_balance = progress.get("score_balance", 0)
    new_balance = old_balance + amount
    progress["score_balance"] = new_balance
    
    # Сохраняем
    storage.save_user(target_id, progress)
    log_audit_action(user_id, "GIVE_BALANCE", f"target={target_id} amount={amount}")
    
    # Сообщение об успехе
    sign = "+" if amount > 0 else ""
    await update.message.reply_text(
        f"✅ **Баланс изменён!**\n\n"
        f"👤 Пользователь: `{target_id}`\n"
        f"💰 Изменение: {sign}{amount:,} золотых\n"
        f"📊 Было: {old_balance:,} → Стало: {new_balance:,}",
        parse_mode="Markdown"
    )
    
    logger.info(f"💰 Admin {user_id} gave {amount} to user {target_id} (balance: {old_balance} → {new_balance})")


async def backup_db_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создаёт бэкап базы данных (админ)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    await update.message.reply_text("⚠️ Используйте /backup из основного файла.")


async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает Telegram ID пользователя"""
    user_id = update.effective_user.id if update.effective_user else 0
    await update.message.reply_text(f"🆔 Твой Telegram ID: `{user_id}`", parse_mode="Markdown")