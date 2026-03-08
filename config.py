# config.py
import os
import re

# Токен бота читается из переменных окружения.
# НЕ храните секреты в коде. Установите BOT_TOKEN в системных переменных
# или в файле .env (не добавляйте .env в репозиторий).
BOT_TOKEN = os.getenv("BOT_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(BASE_DIR, "data", "tasks.json")        # ← ДОБАВЛЕНО
SHARDS_FILE = os.path.join(BASE_DIR, "data", "shards.json")      # ← ДОБАВЛЕНО
PHRASES_FILE = os.path.join(BASE_DIR, "data", "phrases.json")
PROGRESS_FILE = os.path.join(BASE_DIR, "data", "progress.json")
BOSSES_INFO_FILE = os.path.join(BASE_DIR, "data", "bosses_info.json")

# Папки (для будущего использования)
TASKS_DIR = os.path.join(BASE_DIR, "data", "tasks")
BOSS_DATA_DIR = os.path.join(BASE_DIR, "data", "bosses")
SHARDS_DATA_DIR = os.path.join(BASE_DIR, "data", "shards")
# Папка с разбитыми "мир" файлами (worlds)
WORLD_DATA_DIR = os.path.join(BASE_DIR, "data", "worlds")
FINAL_DATA_DIR = os.path.join(BASE_DIR, "data", "final")

# Администраторы (ID) — для dev-команд и читов. Указывай через запятую в переменных окружения.
# Пример: ADMIN_IDS=123456789,987654321
ADMIN_IDS = []
_admins = os.getenv("ADMIN_IDS", "")
if _admins:
    try:
        ADMIN_IDS = [int(x.strip()) for x in _admins.split(",") if x.strip()]
    except ValueError:
        ADMIN_IDS = []


# =============================================================================
# ✅ ВАЛИДАЦИЯ КОНФИГУРАЦИИ (добавлено)
# =============================================================================
def validate_config():
    """
    Проверяет конфигурацию при импорте.
    Выбрасывает понятную ошибку, если что-то не так.
    """
    # Проверка BOT_TOKEN
    if not BOT_TOKEN or not isinstance(BOT_TOKEN, str) or not BOT_TOKEN.strip():
        raise ValueError("❌ BOT_TOKEN не найден или пуст в .env файле!")
    
    # Формат токена: цифры:буквы (пример: 123456789:AAH... )
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', BOT_TOKEN.strip()):
        raise ValueError(f"❌ Неверный формат BOT_TOKEN: {BOT_TOKEN[:10]}...")
    
    # Проверка ADMIN_IDS
    if not ADMIN_IDS or not isinstance(ADMIN_IDS, (list, tuple)):
        raise ValueError(f"❌ ADMIN_IDS должен быть списком целых чисел, получено: {type(ADMIN_IDS)}")
    
    if not all(isinstance(x, int) and x > 0 for x in ADMIN_IDS):
        raise ValueError(f"❌ ADMIN_IDS должен содержать только положительные целые числа: {ADMIN_IDS}")
    
    # Проверка прав на запись в папки
    for dir_path in ["data", "logs"]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        if not os.access(dir_path, os.W_OK):
            raise ValueError(f"❌ Нет прав на запись в папку: {dir_path}")
    
    print("✅ Конфигурация проверена: OK")


# ✅ Автоматический вызов при импорте config
validate_config()