"""
Фикстуры pytest для smoke-тестов web API.
Изолированная SQLite-БД — не трогаем data/progress.db разработчика.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("BOT_TOKEN", "123456789:AAHtesttesttesttesttesttesttest")
os.environ.setdefault("ADMIN_IDS", "999000001")

_TEST_DIR = tempfile.mkdtemp(prefix="chislyandia_pytest_")
_TEST_DB = os.path.join(_TEST_DIR, "progress.db")

from database.schema import init_database

init_database(_TEST_DB)

import database.storage as storage_mod

storage_mod._connection = None
storage_mod.DB_FILE = _TEST_DB
storage_mod.DATA_DIR = _TEST_DIR

from web.api_server import app, storage, engine  # noqa: E402

TEST_USER_ID = "999000001"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def user_id():
    return TEST_USER_ID


@pytest.fixture
def seeded_user(user_id):
    """Игрок с балансом для банка / задач / алхимии."""
    uid = int(user_id)
    user = storage.get_or_create_user(uid, username="pytest", first_name="PyTest")
    user["score_balance"] = 500
    user["total_score"] = 500
    user["unlocked_zones"] = ["addition"]
    user["current_level"] = None
    user["selected_tasks"] = []
    user["current_task_index"] = 0
    user["mistakes_in_level"] = 0
    user["consecutive_errors"] = 0
    user["chaos_energy"] = 0
    storage.save_user(uid, user)
    return user_id
