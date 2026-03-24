# manyunya_bot.py
"""
Основной файл запуска бота «Числяндия».
Версия: 4.7 (Full Restore + run_polling Fix) 🟢🟣✅

Фичи:
- ✅ Поддержка ОБОИХ адаптеров одновременно (Telegram + VK/MAX)
- ✅ Чтение настроек из .env / .env.local
- ✅ Инициализация адаптеров в post_init() с sys.stderr отладкой
- ✅ ВСЕ оригинальные хендлеры восстановлены
- ✅ Сохранение списка адаптеров в bot_data['adapters']
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

# ✅ ПОДДЕРЖКА ДВУХ РЕЖИМОВ
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
    sys.stderr.write("🧪 Запущен ТЕСТОВЫЙ режим (.env.local)\n")
else:
    load_dotenv('.env')
    sys.stderr.write("🚀 Запущен ПРОДАКШН режим (.env)\n")

# === ПОДАВЛЕНИЕ МУСОРНЫХ ЛОГОВ ===
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# === ИМПОРТЫ ДЛЯ SQLITE, АВАТАРОК И SCORE MANAGER ===
from config import BASE_DIR, BOT_TOKEN, ADMIN_IDS, validate_config, IS_PRODUCTION, BACKUP_KEEP_COUNT
from database.schema import init_database
from database.storage import PlayerStorage
from core.avatar_cache import init_avatar_cache
from core.score_manager import ScoreManager
from core.logger import log_bot_start, log_error, setup_logging

# ✅ НОВЫЕ ИМПОРТЫ: ЯДРО, БАНК, ЗАМОК, МАГАЗИН, АРТЕФАКТЫ, НАВИГАЦИЯ, ТАЙНАЯ КОМНАТА
from core.game_engine import ChislyandiaEngine
from handlers.bank import get_bank_handlers
from handlers.castle import get_castle_handlers
from handlers.shop import get_shop_handlers
from handlers.artifacts import get_artifact_handlers
from handlers.navigation import get_navigation_handlers
from handlers.secret_room import get_secret_room_handlers

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

# ✅ ИМПОРТ АДАПТЕРОВ ПЛАТФОРМ (мульти-платформа!)
from platforms.telegram_adapter import TelegramAdapter
from platforms.max_adapter import MaxAdapter

# === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
setup_logging(BASE_DIR, os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# ========================================
# ✅ ФУНКЦИЯ ОТЛАДКИ (через sys.stderr — не глушится!)
# ========================================
def debug_print(msg):
    """Вывод отладки через sys.stderr (не глушится telegram.ext)"""
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

# ========================================
# ✅ POST_INIT (с sys.stderr отладкой)
# ========================================
async def post_init(application: Application):
    # 🔥 ЭТИ СТРОКИ ДОЛЖНЫ ВЫЙТИ ТОЧНО!
    print("\n" + "!" * 70, flush=True)
    print("🚨🚨🚨 POST_INIT НАЧАЛАСЬ! 🚨🚨🚨", flush=True)
    print("!" * 70 + "\n", flush=True)
    logger.info("🚨 POST_INIT НАЧАЛАСЬ!")
    
    application.bot_data['start_time'] = time.time()
    """
    Запускает загрузку аватарок В ФОНЕ.
    Инициализирует ScoreManager, ChislyandiaEngine и АДАПТЕРЫ платформ.
    """
    application.bot_data['start_time'] = time.time()
    
    # === ОТЛАДКА ЧЕРЕЗ sys.stderr ===
    debug_print("\n" + "=" * 70)
    debug_print("🔍🔍🔍 POST_INIT: ПРОВЕРКА .env 🔍🔍🔍")
    debug_print("=" * 70)
    
    bot_token = os.getenv('BOT_TOKEN', '')
    vk_token = os.getenv('VK_TOKEN', '')
    vk_group = os.getenv('VK_GROUP_ID', '')
    
    debug_print(f"BOT_TOKEN: '{bot_token[:20]}...' (длина: {len(bot_token)})")
    debug_print(f"VK_TOKEN: '{vk_token[:20]}...' (длина: {len(vk_token)})")
    debug_print(f"VK_GROUP_ID: '{vk_group}'")
    
    tg_valid = bot_token and len(bot_token) > 30 and ':' in bot_token and not bot_token.startswith('#')
    vk_valid = vk_token and vk_group and len(vk_token) > 20 and not vk_token.startswith('#')
    
    debug_print(f"✅ Telegram токен валиден: {tg_valid}")
    debug_print(f"✅ VK токен валиден: {vk_valid}")
    debug_print("=" * 70 + "\n")
    # ================================
    
    # === ИНИЦИАЛИЗАЦИЯ АДАПТЕРОВ ===
    adapters = []
    
    
    logger.info(f"🔍 Проверка токенов...")
    logger.info(f"   bot_token длина: {len(bot_token)}")
    logger.info(f"   vk_token длина: {len(vk_token)}")
    logger.info(f"   tg_valid: {tg_valid}")
    logger.info(f"   vk_valid: {vk_valid}")
    
    # 1. Telegram
    if tg_valid:
        try:
            debug_print("🔄 Инициализация TelegramAdapter...")
            tg_adapter = TelegramAdapter(application.bot)
            adapters.append(tg_adapter)
            debug_print("✅ TelegramAdapter инициализирован")
            logger.info("✅ TelegramAdapter инициализирован")
        except Exception as e:
            debug_print(f"❌ Ошибка TelegramAdapter: {e}")
            logger.error(f"❌ Ошибка TelegramAdapter: {e}", exc_info=True)
    else:
        debug_print(f"⚠️ Telegram токен не валиден (длина={len(bot_token)})")
    
    # 2. MAX/VK
    if vk_valid:
        try:
            debug_print("🔄 Инициализация MaxAdapter...")
            vk_config = {
                'vk_token': vk_token,
                'vk_version': os.getenv('VK_API_VERSION', '5.131'),
                'group_id': vk_group,
            }
            vk_adapter = MaxAdapter(vk_config)
            adapters.append(vk_adapter)
            debug_print("✅ MaxAdapter инициализирован")
            logger.info("✅ MaxAdapter инициализирован")
        except Exception as e:
            debug_print(f"❌ Ошибка MaxAdapter: {e}")
            logger.error(f"❌ Ошибка MaxAdapter: {e}", exc_info=True)
    else:
        debug_print(f"⚠️ VK настройки не валидны")
    
    # Проверка что хоть один адаптер есть
    if not adapters:
        debug_print("❌ НЕТ НИ ОДНОГО АДАПТЕРА! Проверь .env")
        logger.error("❌ Нет ни одного адаптера! Проверь .env")
    
    # Сохраняем ВСЕ адаптеры + первый для обратной совместимости
    if adapters:
        application.bot_data['adapters'] = adapters
        application.bot_data['adapter'] = adapters[0]
        application.bot_data['platform'] = adapters[0].platform_name
        debug_print(f"✅ Запущено адаптеров: {len(adapters)}")
        for adapter in adapters:
            debug_print(f"   • {adapter.platform_name}")
        logger.info(f"✅ Запущено адаптеров: {len(adapters)}")
        for adapter in adapters:
            logger.info(f"   • {adapter.platform_name}")
    # === КОНЕЦ ИНИЦИАЛИЗАЦИИ АДАПТЕРОВ ===
    # === ДОБАВИТЬ ЭТО В КОНЕЦ post_init() ===
    
    # Лог запуска (ПЕРЕНЕСЁН СЮДА из main!)
    if adapters:
        platform_names = [a.platform_name for a in adapters]
        debug_print(f"\n🤖 БОТ ЗАПУЩЕН! Платформы: {', '.join(platform_names)} 🤖")
        debug_print("🛑 Ctrl+C для остановки\n")
        logger.info(f"🤖 БОТ ЗАПУЩЕН! Платформы: {', '.join(platform_names)} 🤖")
    else:
        debug_print("\n⚠️ БОТ ЗАПУЩЕН БЕЗ АДАПТЕРОВ!")
        logger.info("🤖 БОТ ЗАПУЩЕН! Платформы: нет адаптеров 🤖")
    
    # Аватарки
    debug_print("🎨 Загрузка аватарок...")
    cache = init_avatar_cache(application.bot)
    asyncio.create_task(cache.load_avatars())
    
    # Менеджеры
    storage = application.bot_data.get('storage')
    if storage:
        application.bot_data['score_manager'] = ScoreManager(storage)
        application.bot_data['engine'] = ChislyandiaEngine(storage, application.bot_data['score_manager'])
        debug_print("✅ ScoreManager + Engine OK")
    
    debug_print("✅ Бот готов!\n")
    # =====================================    
    # Загрузка аватарок в фоне
    debug_print("🎨 Загрузка аватарок (в фоне)...")
    logger.info("🎨 Загрузка аватарок (в фоне)...")
    cache = init_avatar_cache(application.bot)
    
    async def load_avatars_safe():
        try:
            result = await cache.load_avatars()
            debug_print(f"✅ Аватарки: {result}")
            logger.info(f"✅ Аватарки: {result}")
        except FileNotFoundError as e:
            debug_print(f"❌ Папка с аватарками не найдена: {e}")
            logger.error(f"❌ Папка с аватарками не найдена: {e}")
        except telegram.error.BadRequest as e:
            debug_print(f"❌ Telegram API ошибка: {e}")
            logger.error(f"❌ Telegram API ошибка: {e}")
        except Exception as e:
            debug_print(f"❌ Ошибка аватарок: {e}")
            logger.error(f"❌ Ошибка аватарок: {e}", exc_info=True)
    
    asyncio.create_task(load_avatars_safe())
    
    # Инициализация менеджеров
    storage = application.bot_data.get('storage')
    if storage:
        score_manager = ScoreManager(storage)
        application.bot_data['score_manager'] = score_manager
        debug_print("✅ ScoreManager инициализирован")
        logger.info("✅ ScoreManager инициализирован")
        
        engine = ChislyandiaEngine(storage, score_manager)
        application.bot_data['engine'] = engine
        debug_print("✅ ChislyandiaEngine (ядро) инициализировано")
        logger.info("✅ ChislyandiaEngine (ядро) инициализировано")
    else:
        debug_print("❌ Storage не найден")
        logger.error("❌ Storage не найден")
    
    debug_print("✅ Бот готов к работе!\n")
    logger.info("✅ Бот готов к работе!\n")


# ========================================
# ✅ КОМАНДЫ (ПОЛНЫЙ НАБОР — ВСЕ ОРИГИНАЛЬНЫЕ)
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
        
        # Ротация бэкапов: храним только последние BACKUP_KEEP_COUNT файлов.
        backups = glob.glob(os.path.join(BASE_DIR, "data", "progress_backup_*.db"))
        backups.sort(key=os.path.getmtime, reverse=True)
        for old in backups[BACKUP_KEEP_COUNT:]:
            try:
                os.remove(old)
            except Exception as rm_err:
                logger.warning(f"⚠️ Не удалось удалить старый бэкап {old}: {rm_err}")
        
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
        with open(os.path.join(BASE_DIR, 'logs', 'app.log'), 'r', encoding='utf-8') as f:
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
    debug_print("\n" + "=" * 60 + "\n🛑 ЗАВЕРШЕНИЕ")
    logger.info("\n" + "=" * 60 + "\n🛑 ЗАВЕРШЕНИЕ")
    
    adapters = application.bot_data.get('adapters', [])
    for adapter in adapters:
        if hasattr(adapter, 'close'):
            try:
                await adapter.close()
            except Exception as e:
                debug_print(f"❌ Ошибка закрытия {adapter.platform_name}: {e}")
                logger.error(f"❌ Ошибка закрытия {adapter.platform_name}: {e}")
    
    storage = application.bot_data.get('storage')
    if storage and hasattr(storage, 'close'):
        storage.close()
    
    debug_print("✅ Бот остановлен корректно")
    logger.info("✅ Бот остановлен корректно")

def graceful_shutdown_sync(signum, frame):
    debug_print("🛑 Сигнал завершения")
    logger.info("🛑 Сигнал завершения")
    sys.exit(0)


# ========================================
# ✅ MAIN (ИСПОЛЬЗУЕМ run_polling!)
# ========================================
def main():
    """Точка входа — используем run_polling() для авто-вызова post_init"""
    
    debug_print("\n🚨🚨🚨 MAIN() ЗАПУЩЕНА! 🚨🚨🚨\n")
    
    log_bot_start()
    validate_config()
    
    signal.signal(signal.SIGINT, graceful_shutdown_sync)
    signal.signal(signal.SIGTERM, graceful_shutdown_sync)
    
    # Получаем токен (для Telegram)
    token = os.getenv('BOT_TOKEN', '')
    if not token or token == '' or token.startswith('#') or len(token) < 30 or ':' not in token:
        token = "000000000:AAHdAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoP"
        debug_print("⚠️ BOT_TOKEN невалиден, заглушка для VK-only")
        logger.warning("⚠️ BOT_TOKEN невалиден, заглушка для VK-only")
    
    # Строим приложение
    app = Application.builder() \
        .token(token) \
        .read_timeout(30) \
        .connect_timeout(30) \
        .post_init(post_init) \
        .post_shutdown(graceful_shutdown_async) \
        .build()
    
    # Настраиваем хранилище
    init_database()
    storage = PlayerStorage()
    app.bot_data['storage'] = storage
    
    # === 1. КОМАНДЫ ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    if not IS_PRODUCTION:
        app.add_handler(CommandHandler("reload_avatars", reload_avatars_cmd))
    app.add_handler(CommandHandler("bosses", show_bosses_guide))
    app.add_handler(CommandHandler("restart", restart_game))
    app.add_handler(CommandHandler("logs", show_logs))
    app.add_handler(CommandHandler("health", health_check))
    
    # === 2. НАВИГАЦИЯ (ПЕРВЫМ!) ===
    app.add_handlers(get_navigation_handlers())
    
    # === 3. СПЕЦИФИЧНЫЕ ХЕНДЛЕРЫ ===
    app.add_handlers(get_bank_handlers())
    app.add_handlers(get_castle_handlers())
    app.add_handlers(get_shop_handlers())
    app.add_handlers(get_artifact_handlers())
    app.add_handlers(get_secret_room_handlers())
    
    # === 4. АДМИН-КОМАНДЫ ===
    if not IS_PRODUCTION:
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
    if not IS_PRODUCTION:
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(universal_callback_handler))
    
    # === 7. ОБРАБОТЧИК ОШИБОК ===
    async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        import traceback
        err = context.error
        user_id = update.effective_user.id if update and update.effective_user else 0
        log_error(user_id, str(err), exc_info=True)
        logger.error("Unhandled exception:", exc_info=err)
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        if IS_PRODUCTION:
            text = f"⚠️ Error:\n{type(err).__name__}: {str(err)[:200]}"
        else:
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
        real_token = os.getenv('BOT_TOKEN', '')
        if real_token and ':' in real_token and len(real_token) > 30:
            webhook_url = f"https://api.telegram.org/bot{real_token}/deleteWebhook?drop_pending_updates=true"
            with urllib.request.urlopen(webhook_url, timeout=5) as resp:
                debug_print(f"Webhook: {resp.read()[:50]}")
    except: pass

    # === ЗАПУСК (РУЧНОЙ ВЫЗОВ post_init + start_polling) ===
    debug_print("\n📡 Запуск polling...")
    
    async def run_bot():
        """Запускает бота с ручным вызовом post_init"""
        
        # 🔥 ВАЖНО: вызываем post_init ВРУЧНУЮ!
        debug_print("🔄 Вызов post_init() вручную...")
        await post_init(app)
        
        debug_print("🔄 app.initialize()...")
        await app.initialize()
        
        debug_print("🔄 app.start()...")
        await app.start()
        
        debug_print("🔄 start_polling()...")
        await app.updater.start_polling(drop_pending_updates=True)
        
        # Держим бота запущенным
        debug_print("✅ Бот работает! Ждём сообщений...")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            debug_print("🔄 Polling cancelled")
        finally:
            debug_print("🔄 Остановка...")
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            debug_print("✅ Бот остановлен")
    
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        debug_print("👋 Остановлено пользователем")
    except Exception as e:
        debug_print(f"❌ Ошибка: {e}")
        import traceback
        debug_print(traceback.format_exc())


if __name__ == "__main__":
    main()