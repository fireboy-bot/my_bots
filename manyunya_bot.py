# manyunya_bot.py
"""
Основной файл запуска бота «Числяндия».
Версия: 2.2 (Замок + Златочёт + Ядро) 🏰🏦🧠🛡️

Интеграция:
- ChislyandiaEngine (ядро игры, мультиплатформенное)
- Златочёт (банк) через ядро
- Замок (экономика декораций) через ядро
- ScoreManager и PlayerStorage
- Корректное закрытие ресурсов при shutdown
- Логирование через logging, пути через BASE_DIR
"""

import logging
import telegram
import asyncio
import os
import shutil
import signal
import sys
import time
import glob
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Загружаем переменные окружения (токен и т.д.)
load_dotenv()

# === ПОДАВЛЕНИЕ МУСОРНЫХ ЛОГОВ ===
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
# ===============================

# === ИМПОРТЫ ДЛЯ SQLITE, АВАТАРОК И SCORE MANAGER ===
from config import BASE_DIR, BOT_TOKEN, ADMIN_IDS, validate_config
from database.schema import init_database
from database.storage import PlayerStorage
from core.avatar_cache import init_avatar_cache
from core.score_manager import ScoreManager
from core.logger import log_bot_start, log_error
# =====================================

# ✅ НОВЫЕ ИМПОРТЫ: ЯДРО, БАНК, ЗАМОК
from core.game_engine import ChislyandiaEngine
from handlers.bank import get_bank_handlers
from handlers.castle import get_castle_handlers

from handlers.commands import start, show_bosses_guide, restart_game, show_logs, health_check
from handlers.message_router import handle_message
from handlers.admin_commands import (
    migrate_cmd, debug_progress_cmd, backup_db_cmd, 
    myid_cmd, dump_user_cmd, reset_user_cmd, give_cmd
)
from handlers.dev_bosses import (
    dev_boss_null, dev_boss_minus, dev_boss_multiply, 
    dev_boss_fracosaur, dev_boss_final, dev_boss_time, 
    dev_boss_measure, dev_boss_logic, dev_boss_true_lord
)
from handlers.universal_callback import universal_callback_handler
from core.ui_helpers import get_persistent_keyboard

# === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'bot.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ========================================
# ✅ ФУНКЦИЯ POST_INIT (загружает аватарки в фоне + инициализирует ядро)
# ========================================
async def post_init(application: Application):
    """
    Запускает загрузку аватарок В ФОНЕ (не блокирует бота).
    Инициализирует ScoreManager и ChislyandiaEngine (ядро).
    """
    # ✅ Метка времени запуска (для health check)
    application.bot_data['start_time'] = time.time()
    
    logger.info("🎨 Запуск загрузки аватарок (в фоне)...")
    cache = init_avatar_cache(application.bot)
    
    # ✅ Создаём задачу в фоне (не ждём завершения!)
    asyncio.create_task(cache.load_avatars())
    
    # ✅ Инициализируем ScoreManager
    storage = application.bot_data.get('storage')
    if storage:
        score_manager = ScoreManager(storage)
        application.bot_data['score_manager'] = score_manager
        logger.info("✅ ScoreManager инициализирован")
        
        # ✅ ИНИЦИАЛИЗИРУЕМ ЯДРО (ChislyandiaEngine)
        engine = ChislyandiaEngine(storage, score_manager)
        application.bot_data['engine'] = engine
        logger.info("✅ ChislyandiaEngine (ядро) инициализировано")
    else:
        logger.error("❌ Не удалось инициализировать ScoreManager: storage не найден")
    
    logger.info("✅ Бот готов к работе! Аватарки грузятся в фоне...\n")


# ========================================
# ✅ НОВАЯ КОМАНДА /reset (АВАРИЙНЫЙ ВЫХОД)
# ========================================
async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Аварийный сброс уровня для пользователей.
    Если бот застрял или уровень не завершается — эта команда поможет.
    """
    try:
        user_id = update.effective_user.id if update.effective_user else 0
        first_name = update.effective_user.first_name if update.effective_user else "Пользователь"
        
        logger.info(f"🔄 RESET вызван: user_id={user_id}, name={first_name}")
        
        storage = context.bot_data.get('storage')
        if not storage:
            await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
            return
        
        user_data = storage.get_user(user_id) or {}
        
        # Сбрасываем все активные состояния
        user_data.update({
            "current_level": None,
            "selected_tasks": [],
            "current_task_index": 0,
            "in_boss_battle": False,
            "current_boss": None,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "mistakes_in_level": 0,
            "boss_health": 5,
            "boss_abilities_used": []
        })
        storage.save_user(user_id, user_data)
        
        await update.message.reply_text(
            f"✅ {first_name}, уровень сброшен! Возвращаюсь в меню.",
            reply_markup=get_persistent_keyboard(user_data)
        )
        
        logger.info(f"✅ RESET завершён: user_id={user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в /reset: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Ошибка при сбросе. Попробуй /start или напиши администратору."
        )


# ========================================
# ✅ НОВАЯ КОМАНДА /help (СПРАВКА)
# ========================================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает справку по командам"""
    help_text = (
        "📚 **СПРАВКА ПО КОМАНДАМ**\n\n"
        "🎮 **Игровые команды**:\n"
        "/start — Начать игру / Главное меню\n"
        "/reset — Сбросить текущий уровень (если застрял)\n"
        "/bank — Открыть Златочёт (банк)\n"
        "/deposit <сумма> — Положить золото в банк\n"
        "/withdraw — Забрать вклад с процентами\n"
        "/castle — Показать состояние Замка\n"
        "/pay_upkeep [дни] — Оплатить upkeep Замка\n\n"
        "📊 **Информация**:\n"
        "/health — Проверка состояния бота\n"
        "/logs — Последние логи (для админов)\n\n"
        "💡 **Совет**:\n"
        "Используй кнопку *⬅️ Назад* чтобы выйти из уровня или боя!"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


# ========================================
# ✅ КОМАНДА /backup (бэкап базы)
# ========================================
async def backup_db_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создаёт бэкап базы данных (только для админа)"""
    
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    
    try:
        db_path = os.path.join(BASE_DIR, "data", "progress.db")
        
        if not os.path.exists(db_path):
            await update.message.reply_text(f"❌ База данных не найдена: `{db_path}`", parse_mode="Markdown")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BASE_DIR, "data", f"progress_backup_{timestamp}.db")
        
        shutil.copy2(db_path, backup_path)
        file_size = os.path.getsize(backup_path) / 1024
        
        await update.message.reply_text(
            f"✅ **Бэкап создан!**\n\n"
            f"📁 Файл: `{os.path.basename(backup_path)}`\n"
            f"📂 Путь: `{os.path.dirname(backup_path)}`\n"
            f"💾 Размер: {file_size:.1f} КБ",
            parse_mode="Markdown"
        )
        
        logger.info(f"💾 Бэкап создан: {backup_path}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка бэкапа: {e}")
        await update.message.reply_text(f"❌ Ошибка создания бэкапа: {e}")


# ========================================
# ✅ КОМАНДА /restore (восстановление)
# ========================================
async def restore_db_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Восстанавливает базу из последнего бэкапа (только для админа)"""
    
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    
    try:
        db_path = os.path.join(BASE_DIR, "data", "progress.db")
        
        backup_pattern = os.path.join(BASE_DIR, "data", "progress_backup_*.db")
        backups = glob.glob(backup_pattern)
        
        if not backups:
            await update.message.reply_text("⚠️ Бэкапы не найдены!")
            return
        
        backups.sort(reverse=True)
        latest_backup = backups[0]
        
        shutil.copy2(latest_backup, db_path)
        
        await update.message.reply_text(
            f"✅ **База восстановлена!**\n\n"
            f"📁 Из: `{os.path.basename(latest_backup)}`\n\n"
            f"⚠️ _Перезапустите бота для применения изменений._",
            parse_mode="Markdown"
        )
        
        logger.info(f"💾 База восстановлена из: {latest_backup}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка восстановления: {e}")
        await update.message.reply_text(f"❌ Ошибка восстановления: {e}")


# ========================================
# ✅ КОМАНДА /list_backups (список бэкапов)
# ========================================
async def list_backups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список бэкапов (только для админа)"""
    
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    
    try:
        backup_pattern = os.path.join(BASE_DIR, "data", "progress_backup_*.db")
        
        backups = glob.glob(backup_pattern)
        
        if not backups:
            await update.message.reply_text("⚠️ Бэкапы не найдены!")
            return
        
        backups.sort(reverse=True)
        
        text = "📦 **СОХРАНЁННЫЕ БЭКАПЫ:**\n\n"
        for i, backup in enumerate(backups[:10], 1):
            file_size = os.path.getsize(backup) / 1024
            filename = os.path.basename(backup)
            text += f"{i}. `{filename}` ({file_size:.1f} КБ)\n"
        
        if len(backups) > 10:
            text += f"\n_... и ещё {len(backups) - 10} бэкапов_"
        
        text += f"\n\n📂 _Папка: `{os.path.join(BASE_DIR, 'data')}`_"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Ошибка списка бэкапов: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


# ========================================
# ✅ GRACEFUL SHUTDOWN (корректное завершение)
# ========================================
async def graceful_shutdown_async(application: Application):
    """
    Асинхронное корректное завершение работы бота.
    Закрывает БД и другие ресурсы.
    """
    logger.info("\n" + "=" * 60)
    logger.info("🛑 ПОЛУЧЕН СИГНАЛ ЗАВЕРШЕНИЯ")
    logger.info("=" * 60)
    
    # Закрываем хранилище
    storage = application.bot_data.get('storage')
    if storage and hasattr(storage, 'close'):
        storage.close()
        logger.info("✅ PlayerStorage закрыт")
    
    # ScoreManager и Engine не требуют явного закрытия (используют storage)
    
    logger.info("✅ Состояние сохранено")
    logger.info("👋 До свидания! Бот остановлен корректно.")
    logger.info("=" * 60)


def graceful_shutdown_sync(signum, frame):
    """
    Синхронный обработчик сигналов (fallback).
    """
    logger.info("🛑 Синхронный сигнал завершения (SIGINT/SIGTERM)")
    sys.exit(0)


# === ЗАПУСК ===
def main():
    # Логируем старт бота
    log_bot_start()
    
    # ✅ ПРОВЕРКА КОНФИГУРАЦИИ (валидация .env)
    validate_config()
    
    # ✅ РЕГИСТРИРУЕМ ОБРАБОТЧИКИ СИГНАЛОВ
    signal.signal(signal.SIGINT, graceful_shutdown_sync)
    signal.signal(signal.SIGTERM, graceful_shutdown_sync)
    
    # Создаём приложение с таймаутами и post_init
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .read_timeout(30) \
        .connect_timeout(30) \
        .post_init(post_init) \
        .post_shutdown(graceful_shutdown_async) \
        .build()
    
    # ========================================
    # ✅ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
    # ========================================
    init_database()
    storage = PlayerStorage()
    app.bot_data['storage'] = storage
    # ScoreManager и Engine инициализируются в post_init
    # ========================================
    
    # === ОБЫЧНЫЕ КОМАНДЫ ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("bosses", show_bosses_guide))
    app.add_handler(CommandHandler("restart", restart_game))
    app.add_handler(CommandHandler("logs", show_logs))
    app.add_handler(CommandHandler("health", health_check))
    
    # === ЗЛАТОЧЁТ (БАНК) ===
    app.add_handlers(get_bank_handlers())
    
    # === ЗАМОК (ЭКОНОМИКА) ===
    app.add_handlers(get_castle_handlers())
    
    # === АДМИН-КОМАНДЫ ===
    app.add_handler(CommandHandler("migrate_progress", migrate_cmd))
    app.add_handler(CommandHandler("debug_progress", debug_progress_cmd))
    app.add_handler(CommandHandler("backup_db", backup_db_cmd))
    app.add_handler(CommandHandler("myid", myid_cmd))
    app.add_handler(CommandHandler("dump_user", dump_user_cmd))
    app.add_handler(CommandHandler("reset_user", reset_user_cmd))
    app.add_handler(CommandHandler("give", give_cmd))
    
    # === КОМАНДЫ БЭКАПА ===
    app.add_handler(CommandHandler("backup", backup_db_cmd))
    app.add_handler(CommandHandler("restore", restore_db_cmd))
    app.add_handler(CommandHandler("list_backups", list_backups_cmd))
    
    # === КОМАНДЫ РАЗРАБОТЧИКА (БОССЫ) ===
    app.add_handler(CommandHandler("boss_null", dev_boss_null))
    app.add_handler(CommandHandler("boss_minus", dev_boss_minus))
    app.add_handler(CommandHandler("boss_multiply", dev_boss_multiply))
    app.add_handler(CommandHandler("boss_fracosaur", dev_boss_fracosaur))
    app.add_handler(CommandHandler("boss_final", dev_boss_final))
    app.add_handler(CommandHandler("boss_time", dev_boss_time))
    app.add_handler(CommandHandler("boss_measure", dev_boss_measure))
    app.add_handler(CommandHandler("boss_logic", dev_boss_logic))
    app.add_handler(CommandHandler("boss_true_lord", dev_boss_true_lord))
    
    # === ОБРАБОТЧИКИ СООБЩЕНИЙ И КОЛЛБЭКОВ ===
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(universal_callback_handler))
    
    # === ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК ===
    async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        import traceback
        err = context.error
        user_id = update.effective_user.id if update and update.effective_user else 0
        
        log_error(user_id, str(err), exc_info=True)
        
        logger.error("Unhandled exception:", exc_info=err)
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        text = f"⚠️ Error in bot:\n{str(err)}\n\n{tb[:1500]}"
        for admin in ADMIN_IDS:
            try:
                await app.bot.send_message(admin, text)
            except Exception:
                logger.exception("Failed to notify admin")
    app.add_error_handler(global_error_handler)
    
    # === УДАЛЕНИЕ WEBHOOK (для polling) ===
    try:
        import urllib.request
        import urllib.error
        if BOT_TOKEN:
            webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
            try:
                with urllib.request.urlopen(webhook_url, timeout=5) as resp:
                    logger.info("deleteWebhook response: %s", resp.read()[:200])
            except urllib.error.URLError as e:
                logger.warning("Не удалось удалить webhook синхронно: %s", e)
    except Exception:
        logger.exception("Ошибка при попытке удалить webhook синхронно (игнорируем).")

    logger.info("🤖 Бот запущен! База: SQLite 🗄️ | Очки: ScoreManager 💰 | Ядро: ChislyandiaEngine 🧠 | Златочёт: 🏦 | Замок: 🏰")
    logger.info("🛑 Для остановки нажмите Ctrl+C (корректное завершение)")
    
    try:
        app.run_polling(drop_pending_updates=True)
    except telegram.error.Conflict as e:
        logger.error("Conflict detected while polling: %s", e)
        logger.error("Возможна запущенная другая инстанция бота или активный webhook.")
        raise


if __name__ == "__main__":
    main()