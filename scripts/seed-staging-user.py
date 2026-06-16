#!/usr/bin/env python3
"""Создать демо-пользователя на staging."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.schema import init_database
from database.storage import PlayerStorage

init_database("data/progress.db")
storage = PlayerStorage()
user = storage.get_or_create_user(331113480, username="staging", first_name="Player")
user["score_balance"] = 318
user["total_score"] = 318
user["unlocked_zones"] = ["addition"]
storage.save_user(331113480, user)
print("user ok", user["score_balance"])
