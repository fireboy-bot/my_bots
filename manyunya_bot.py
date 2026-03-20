# manyunya_bot.py
"""
Основной файл запуска бота «Числяндия».
Версия: 3.7 (Fix: Secret Room Handler Registration) 🏰🏦🧠🛡️🔀🎨💰🔮🧭🖼️🗝️✅

Исправление:
- ✅ УДАЛЕНА строка app.add_handlers() из импортов (вызывала NameError)
- ✅ Хендлеры Тайной комнаты регистрируются ВНУТРИ main()
- ✅ Глобальная навигация перехватывает «⬅️ Назад» ПЕРВОЙ
- ✅ Порядок хендлеров: навигация → специфичные → общие
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

# ✅ ПОДДЕРЖКА ДВУХ РЕЖИМОВ: ТЕСТОВЫЙ / ПРОДАКШН
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
    print("🧪 Запущен ТЕСТОВЫЙ режим (.env.local)")
else:
    load_dotenv('.env')
    print("🚀 Запущен ПРОДАКШН режим (.env)")

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

# ✅ НОВЫЕ ИМПОРТЫ: ЯДРО, БАНК, ЗАМОК, МАГАЗИН, АРТЕФАКТЫ, НАВИГАЦИЯ, ТАЙНАЯ КОМНАТА, АДАПТЕРЫ
from core.game_engine import ChislyandiaEngine
from handlers.bank import get_bank_handlers
from handlers.castle import get_castle_handlers
from handlers.shop import get_shop_handlers
from handlers.artifacts import get_artifact_handlers
from handlers.navigation import get_navigation_handlers
from handlers.secret_room import get_secret_room_handlers  # ✅ ИМПОРТ (только импорт!)

from handlers.commands import start, show_bosses_guide, restart_game, show_logs, health_check
from handlers.message_router import handle_message
from handlers.admin_commands import (
    migrate_cmd, debug_progress_cmd, backup_db_cmd, 
    myid_cmd, dump_user_cmd, reset_user_cmd, give_cmd,
    give_balance_cmd
)
from handlers.dev_bosses import (
    dev_boss_null, dev_boss_minus, dev_boss_multiply, 
    dev_boss_fracosaur, dev_boss_final, dev_boss_time, 
    dev_boss_measure, dev_boss_logic, dev_boss_true_lord
)
from handlers.universal_callback import universal_callback_handler
from core.ui_helpers import get_persistent_keyboard

# ✅ ИМПОРТ АДАПТЕРА ПЛАТФОРМЫ
from platforms.telegram_adapter import TelegramAdapter
# ========================================

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
# ✅ ФУНКЦИЯ POST_INIT (с адаптером платформы)
# ========================================
async def post_init(application: Application):
    """
    Запускает загрузку аватарок В ФОНЕ с обработкой ошибок.
    Инициализирует ScoreManager, ChislyandiaEngine (ядро) и АДАПТЕР платформы.
    """
    application.bot_data['start_time'] = time.time()
    
    # ✅ Инициализация адаптера платформы (Telegram)
    telegram_adapter = TelegramAdapter(application.bot)
    application.bot_data['adapter'] = telegram_adapter
    application.bot_data['platform'] = 'telegram'
    logger.info("✅ TelegramAdapter инициализирован")
    
    logger.info("🎨 Запуск загрузки аватарок (в фоне)...")
    cache = init_avatar_cache(application.bot)
    
    async def load_avatars_safe():
        try:
            result = await cache.load_avatars()
            logger.info(f"✅ Аватарки загружены: {result}")
        except FileNotFoundError as e:
            logger.error(f"❌ Папка с аватарками не найдена: {e}")
        except telegram.error.BadRequest as e:
            logger.error(f"❌ Telegram API ошибка (аватарка): {e}")
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка загрузки аватарок: {e}", exc_info=True)
    
    asyncio.create_task(load_avatars_safe())
    
    storage = application.bot_data.get('storage')
    if storage:
        score_manager = ScoreManager(storage)
        application.bot_data['score_manager'] = score_manager
        logger.info("✅ ScoreManager инициализирован")
        
        engine = ChislyandiaEngine(storage, score_manager)
        application.bot_data['engine'] = engine
        logger.info("✅ ChislyandiaEngine (ядро) инициализировано")
    else:
        logger.error("❌ Не удалось инициализировать ScoreManager: storage не найден")
    
    logger.info("✅ Бот готов к работе!\n")


# ========================================
# ✅ КОМАНДЫ (без изменений)
# ========================================
async def reload_avatars_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    try:
        await update.message.reply_text("🎨 Перезагрузка аватарок...")
        cache = init_avatar_cache(context.bot)
        result = await cache.load_avatars()
        await update.message.reply_text(f"✅ Аватарки перезагружены! Результат: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка /reload_avatars: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id if update.effective_user else 0
        first_name = update.effective_user.first_name if update.effective_user else "Пользователь"
        storage = context.bot_data.get('storage')
        if not storage:
            await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
            return
        user_data = storage.get_user(user_id) or {}
        user_data.update({
            "current_level": None, "selected_tasks": [], "current_task_index": 0,
            "in_boss_battle": False, "current_boss": None, "selected_boss_tasks": [],
            "boss_task_index": 0, "mistakes_in_level": 0, "boss_health": 5, "boss_abilities_used": []
        })
        storage.save_user(user_id, user_data)
        await update.message.reply_text(f"✅ {first_name}, уровень сброшен!", reply_markup=get_persistent_keyboard(user_data))
    except Exception as e:
        logger.error(f"❌ Ошибка в /reset: {e}")
        await update.message.reply_text("⚠️ Ошибка при сбросе.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "📚 **СПРАВКА**\n\n🎮 /start — Меню\n/shop — Магазин\n/castle — Замок\n/bank — Банк\n/artifacts — Артефакты\n/back — Выход из уровня\n/reset — Сброс уровня"
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def backup_db_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    try:
        db_path = os.path.join(BASE_DIR, "data", "progress.db")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BASE_DIR, "data", f"progress_backup_{timestamp}.db")
        shutil.copy2(db_path, backup_path)
        await update.message.reply_text(f"✅ Бэкап создан: `{os.path.basename(backup_path)}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def restore_db_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    try:
        db_path = os.path.join(BASE_DIR, "data", "progress.db")
        backups = glob.glob(os.path.join(BASE_DIR, "data", "progress_backup_*.db"))
        if not backups:
            await update.message.reply_text("⚠️ Бэкапы не найдены!")
            return
        backups.sort(reverse=True)
        shutil.copy2(backups[0], db_path)
        await update.message.reply_text(f"✅ База восстановлена!\n⚠️ Перезапустите бота.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def list_backups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    try:
        backups = glob.glob(os.path.join(BASE_DIR, "data", "progress_backup_*.db"))
        if not backups:
            await update.message.reply_text("⚠️ Бэкапы не найдены!")
            return
        text = "📦 **БЭКАПЫ**:\n" + "\n".join([f"{i}. `{os.path.basename(b)}`" for i, b in enumerate(backups[:10], 1)])
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    try:
        with open(os.path.join(BASE_DIR, 'logs', 'bot.log'), 'r', encoding='utf-8') as f:
            logs = f.readlines()[-20:]
        await update.message.reply_text("```\n" + "".join(logs) + "```", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Лог не найден")

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🔒 Только для администратора!")
        return
    status = "🏥 **БОТ ОК**\n"
    if context.bot_data.get('start_time'):
        uptime = int(time.time() - context.bot_data['start_time'])
        status += f"⏱️ Время работы: {uptime // 3600}ч {(uptime % 3600) // 60}м\n"
    status += "✅ Все системы работают"
    await update.message.reply_text(status, parse_mode="Markdown")


# ========================================
# ✅ GRACEFUL SHUTDOWN
# ========================================
async def graceful_shutdown_async(application: Application):
    logger.info("\n" + "=" * 60 + "\n🛑 ЗАВЕРШЕНИЕ")
    adapter = application.bot_data.get('adapter')
    if adapter and hasattr(adapter, 'close'):
        await adapter.close()
    storage = application.bot_data.get('storage')
    if storage and hasattr(storage, 'close'):
        storage.close()
    logger.info("✅ Бот остановлен корректно")

def graceful_shutdown_sync(signum, frame):
    logger.info("🛑 Сигнал завершения")
    sys.exit(0)


# === ЗАПУСК ===
def main():
    log_bot_start()
    validate_config()
    signal.signal(signal.SIGINT, graceful_shutdown_sync)
    signal.signal(signal.SIGTERM, graceful_shutdown_sync)
    
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .read_timeout(30) \
        .connect_timeout(30) \
        .post_init(post_init) \
        .post_shutdown(graceful_shutdown_async) \
        .build()
    
    init_database()
    storage = PlayerStorage()
    app.bot_data['storage'] = storage
    
    # === 1. КОМАНДЫ ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("reload_avatars", reload_avatars_cmd))
    app.add_handler(CommandHandler("bosses", show_bosses_guide))
    app.add_handler(CommandHandler("restart", restart_game))
    app.add_handler(CommandHandler("logs", show_logs))
    app.add_handler(CommandHandler("health", health_check))
    
    # === 2. НАВИГАЦИЯ (ПЕРВЫМ! перехватывает «⬅️ Назад» везде) ===
    app.add_handlers(get_navigation_handlers())
    
    # === 3. СПЕЦИФИЧНЫЕ ХЕНДЛЕРЫ ===
    # ✅ Банк
    app.add_handlers(get_bank_handlers())
    # ✅ Замок
    app.add_handlers(get_castle_handlers())
    # ✅ Магазин
    app.add_handlers(get_shop_handlers())
    # ✅ Артефакты
    app.add_handlers(get_artifact_handlers())
    # ✅ Тайная комната (НОВОЕ!)
    app.add_handlers(get_secret_room_handlers())
    
    # === 4. АДМИН-КОМАНДЫ ===
    app.add_handler(CommandHandler("migrate_progress", migrate_cmd))
    app.add_handler(CommandHandler("debug_progress", debug_progress_cmd))
    app.add_handler(CommandHandler("backup_db", backup_db_cmd))
    app.add_handler(CommandHandler("myid", myid_cmd))
    app.add_handler(CommandHandler("dump_user", dump_user_cmd))
    app.add_handler(CommandHandler("reset_user", reset_user_cmd))
    app.add_handler(CommandHandler("give", give_cmd))
    app.add_handler(CommandHandler("give_balance", give_balance_cmd))
    app.add_handler(CommandHandler("backup", backup_db_cmd))
    app.add_handler(CommandHandler("restore", restore_db_cmd))
    app.add_handler(CommandHandler("list_backups", list_backups_cmd))
    
    # === 5. БОССЫ ===
    app.add_handler(CommandHandler("boss_null", dev_boss_null))
    app.add_handler(CommandHandler("boss_minus", dev_boss_minus))
    app.add_handler(CommandHandler("boss_multiply", dev_boss_multiply))
    app.add_handler(CommandHandler("boss_fracosaur", dev_boss_fracosaur))
    app.add_handler(CommandHandler("boss_final", dev_boss_final))
    app.add_handler(CommandHandler("boss_time", dev_boss_time))
    app.add_handler(CommandHandler("boss_measure", dev_boss_measure))
    app.add_handler(CommandHandler("boss_logic", dev_boss_logic))
    app.add_handler(CommandHandler("boss_true_lord", dev_boss_true_lord))
    
    # === 6. ОБЩИЕ ОБРАБОТЧИКИ (ПОСЛЕДНИМИ!) ===
    # ✅ MessageHandler — должен быть ПОСЛЕ всех специфичных!
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # ✅ CallbackQueryHandler — для inline-кнопок
    app.add_handler(CallbackQueryHandler(universal_callback_handler))
    
    # === 7. ОБРАБОТЧИК ОШИБОК ===
    async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        import traceback
        err = context.error
        user_id = update.effective_user.id if update and update.effective_user else 0
        log_error(user_id, str(err), exc_info=True)
        logger.error("Unhandled exception:", exc_info=err)
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        text = f"⚠️ Error:\n{str(err)}\n\n{tb[:1500]}"
        for admin in ADMIN_IDS:
            try:
                await app.bot.send_message(admin, text)
            except:
                pass
    app.add_error_handler(global_error_handler)
    
    # === УДАЛЕНИЕ WEBHOOK ===
    try:
        import urllib.request
        if BOT_TOKEN:
            webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
            with urllib.request.urlopen(webhook_url, timeout=5) as resp:
                logger.info("Webhook deleted: %s", resp.read()[:100])
    except Exception as e:
        logger.warning(f"Webhook cleanup warning: {e}")

    logger.info("🤖 Бот запущен! Адаптер: Telegram 🤖 | Навигация: ✅ | Артефакты: ✅ | Тайная комната: ✅")
    logger.info("🛑 Ctrl+C для остановки")
    
    try:
        app.run_polling(drop_pending_updates=True)
    except telegram.error.Conflict as e:
        logger.error(f"Conflict: {e}")
        raise


if __name__ == "__main__":
    main()