#!/usr/bin/env python3
"""Создать демо-пользователя на staging (только если ещё нет прогресса)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.schema import init_database
from database.storage import PlayerStorage

DEMO_USER_ID = 331113480

init_database("data/progress.db")
storage = PlayerStorage()

existing = storage.get_user(DEMO_USER_ID)
if existing and (
    existing.get("tasks_solved", 0) > 0
    or len(existing.get("defeated_bosses") or []) > 0
    or len(existing.get("unlocked_zones") or ["addition"]) > 1
):
    print("user ok existing", existing.get("score_balance"))
    sys.exit(0)

user = storage.get_or_create_user(DEMO_USER_ID, username="staging", first_name="Player")
user["score_balance"] = 318
user["total_score"] = 318
user["unlocked_zones"] = ["addition"]
storage.save_user(DEMO_USER_ID, user)
print("user ok new", user["score_balance"])
