#!/usr/bin/env python3
"""
Настройка демо-пользователя для staging-тестов (полный пост-гейм, без победы над True Lord).

Запуск на VPS (после деплоя):
  cd /opt/chislyandia && ./venv/bin/python scripts/configure-demo-user.py

Локально:
  python scripts/configure-demo-user.py
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.schema import init_database
from database.storage import PlayerStorage

DEMO_USER_ID = 331113480

KEEPERS = ["time_keeper", "measure_keeper", "logic_keeper"]
POSTGAME_WORLDS = ["time_world", "measure_world", "logic_world"]


def apply_demo_profile(storage: PlayerStorage, user_id: int) -> None:
    user = storage.get_or_create_user(user_id, username="staging", first_name="Player")

    defeated = set(user.get("defeated_bosses") or [])
    defeated.update(["final_boss", *KEEPERS])
    # Не добавляем true_lord — чтобы можно было тестировать эпик-бой

    unlocked = set(user.get("unlocked_zones") or ["addition"])
    unlocked.update(
        {
            "addition",
            "subtraction",
            "multiplication",
            "division",
            "secret_level",
            "true_lord",
            *POSTGAME_WORLDS,
        }
    )

    completed = set(user.get("completed_zones") or [])
    completed.update(POSTGAME_WORLDS)
    for keeper in KEEPERS:
        completed.add(f"boss_{keeper}")

    user.update(
        {
            "score_balance": max(int(user.get("score_balance", 0)), 5000),
            "total_score": max(int(user.get("total_score", 0)), 5000),
            "defeated_bosses": sorted(defeated),
            "unlocked_zones": sorted(unlocked),
            "completed_zones": sorted(completed),
            "completed_normal_game": True,
            "in_boss_battle": False,
            "current_boss": None,
            "true_lord_epic": False,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "boss_health": 0,
            "boss_max_health": 0,
        }
    )
    storage.save_user(user_id, user)
    print(f"demo user {user_id} configured")
    print(f"  defeated_bosses: {user['defeated_bosses']}")
    print(f"  true_lord unlocked: {'true_lord' in (user.get('unlocked_zones') or [])}")
    print(f"  score_balance: {user['score_balance']}")


def main() -> int:
    init_database("data/progress.db")
    storage = PlayerStorage()
    apply_demo_profile(storage, DEMO_USER_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
