# core/logger.py
"""
Модуль логирования для бота «Числяндия».
Версия: с ротацией файлов + timezone fix 🔄⏱️
"""

import logging
import os
from datetime import datetime, timezone  # ✅ ДОБАВЛЕНО timezone
import traceback
from logging.handlers import RotatingFileHandler

# Создаём папку для логов
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Имя файла лога на сегодня (для имён файлов можно оставить локальное время)
log_filename = f"bot_{datetime.now().strftime('%Y%m%d')}.log"
log_path = os.path.join(LOG_DIR, log_filename)

# ✅ РОТАЦИЯ: 5 МБ на файл, хранить 3 последних
log_handler = RotatingFileHandler(
    log_path,
    encoding='utf-8',
    maxBytes=5*1024*1024,  # 5 МБ
    backupCount=3           # 3 файла
)

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        log_handler,  # В файл (с ротацией)
        logging.StreamHandler()  # В консоль
    ]
)

logger = logging.getLogger("chislyandiya_bot")

def log_user_action(user_id, action, details=""):
    """Логирует действия пользователя"""
    try:
        logger.info(f"USER {user_id} | {action} | {details}")
    except Exception as e:
        print(f"Logger error: {e}")

def log_error(user_id, error_msg, exc_info=None):
    """Логирует ошибки с трейсбэком"""
    try:
        logger.error(f"USER {user_id} | ERROR: {error_msg}")
        if exc_info:
            logger.error(traceback.format_exc())
    except Exception as e:
        print(f"Logger error: {e}")

def log_bot_start():
    """Логирует запуск бота с UTC временем"""
    # ✅ Используем timezone.utc для консистентности
    utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    logger.info("=" * 60)
    logger.info(f"🤖 БОТ ЗАПУЩЕН | {utc_now}")
    logger.info("=" * 60)

def get_today_logs():
    """Возвращает последние 100 строк лога сегодняшнего дня"""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return ''.join(lines[-100:])
    except Exception as e:
        return f"Ошибка чтения лога: {e}"