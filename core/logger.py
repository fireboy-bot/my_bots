# core/logger.py
"""
Модуль логирования для бота «Числяндия».
Разделяет логи на app/error/audit/user_activity.
"""

import logging
import os
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

_configured = False

APP_LOGGER_NAME = "chislyandiya.app"
ERROR_LOGGER_NAME = "chislyandiya.error"
AUDIT_LOGGER_NAME = "chislyandiya.audit"
USER_LOGGER_NAME = "chislyandiya.user"


def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def setup_logging(base_dir: str = ".", log_level: str = "INFO"):
    """Единая точка настройки логирования."""
    global _configured
    if _configured:
        return

    logs_dir = os.path.join(base_dir, "logs")
    _ensure_dir(logs_dir)

    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger для обычных модульных logger = logging.getLogger(__name__)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    app_handler = RotatingFileHandler(
        os.path.join(logs_dir, "app.log"),
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    app_handler.setLevel(level)
    app_handler.setFormatter(fmt)
    root.addHandler(app_handler)

    error_handler = RotatingFileHandler(
        os.path.join(logs_dir, "error.log"),
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)
    root.addHandler(error_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    # Отдельный audit logger
    audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
    audit_logger.setLevel(logging.INFO)
    audit_logger.handlers.clear()
    audit_logger.propagate = False
    audit_handler = RotatingFileHandler(
        os.path.join(logs_dir, "audit.log"),
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    audit_handler.setFormatter(fmt)
    audit_logger.addHandler(audit_handler)

    # Отдельный user activity logger (без сырых текстов)
    user_logger = logging.getLogger(USER_LOGGER_NAME)
    user_logger.setLevel(logging.INFO)
    user_logger.handlers.clear()
    user_logger.propagate = False
    user_handler = RotatingFileHandler(
        os.path.join(logs_dir, "user_activity.log"),
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    user_handler.setFormatter(fmt)
    user_logger.addHandler(user_handler)

    _configured = True


def log_user_action(user_id, action, details=""):
    """Логирует действия пользователя в user_activity.log."""
    try:
        logger = logging.getLogger(USER_LOGGER_NAME)
        logger.info(f"user_id={user_id} action={action} details={details}")
    except Exception as e:
        print(f"Logger error: {e}")


def log_audit_action(actor_user_id, action, details=""):
    """Логирует админ/аудит действия в audit.log."""
    try:
        logger = logging.getLogger(AUDIT_LOGGER_NAME)
        logger.info(f"actor={actor_user_id} action={action} details={details}")
    except Exception as e:
        print(f"Logger error: {e}")


def log_error(user_id, error_msg, exc_info=None):
    """Логирует ошибки в error.log."""
    try:
        logger = logging.getLogger(ERROR_LOGGER_NAME)
        logger.error(f"user_id={user_id} error={error_msg}")
        if exc_info:
            logger.error(traceback.format_exc())
    except Exception as e:
        print(f"Logger error: {e}")


def log_bot_start():
    """Логирует запуск бота с UTC временем."""
    logger = logging.getLogger(APP_LOGGER_NAME)
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info("=" * 60)
    logger.info(f"🤖 БОТ ЗАПУЩЕН | {utc_now}")
    logger.info("=" * 60)


def get_today_logs(base_dir: str = "."):
    """Возвращает последние 100 строк app.log."""
    try:
        path = os.path.join(base_dir, "logs", "app.log")
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-100:])
    except Exception as e:
        return f"Ошибка чтения лога: {e}"