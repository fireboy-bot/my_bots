# handlers/admin_commands.py
"""
Админ-команды для бота «Числяндия».
Версия: SQLite + PlayerStorage 🗄️
"""

import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS

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
    
    # ✅ ИСПРАВЛЕНО: используем storage из bot_data
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    # ✅ ИСПРАВЛЕНО: get_user вместо get_progress
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
    
    # Получаем ID целевого пользователя (если указан)
    if context.args:
        target_id = int(context.args[0]) if context.args[0].isdigit() else user_id
    else:
        target_id = user_id
    
    progress = storage.get_user(target_id) or {}
    
    import json
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
        await update.message.reply_text("Использование: /give @username item_id")
        return
    
    # Парсинг аргументов
    target = context.args[0]
    item_id = context.args[1]
    
    # Получаем user_id из username (упрощённо)
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
    
    await update.message.reply_text(f"✅ Предмет {item_id} выдан пользователю {target_id}.")

async def backup_db_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создаёт бэкап базы данных (админ)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора.")
        return
    
    # Эта команда теперь дублируется в manyunya_bot.py
    await update.message.reply_text("⚠️ Используйте /backup из основного файла.")

async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает Telegram ID пользователя"""
    user_id = update.effective_user.id if update.effective_user else 0
    await update.message.reply_text(f"🆔 Твой Telegram ID: `{user_id}`", parse_mode="Markdown")