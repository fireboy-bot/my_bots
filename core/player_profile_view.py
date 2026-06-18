"""
Сводка профиля игрока для Web API (без Telegram).
"""

from typing import Any, Dict, List, Optional, Tuple

MAIN_ISLANDS = ["addition", "subtraction", "multiplication", "division"]
POST_GAME_WORLDS = ["time_world", "measure_world", "logic_world"]

LEVEL_TITLES = [
    (0, 1, "Ученик"),
    (500, 6, "Исследователь"),
    (2000, 11, "Матемаг"),
    (5000, 16, "Хранитель Чисел"),
    (12000, 21, "Владыка Числяндии"),
]


def get_rank_title(total_score: int) -> Tuple[int, str]:
    for score, level_num, title in reversed(LEVEL_TITLES):
        if total_score >= score:
            return level_num, title
    return 1, "Ученик"


def get_accuracy_stats(tasks_correct: int, tasks_solved: int) -> Dict[str, Any]:
    if tasks_solved <= 0:
        return {
            "percent": 0,
            "label": "🌱 Новичок",
            "emoji": "🔴",
        }

    percent = int((tasks_correct / tasks_solved) * 100)
    if percent >= 90:
        label, emoji = "🌟 Золотой уровень", "🟢"
    elif percent >= 75:
        label, emoji = "🥈 Серебряный уровень", "🟡"
    elif percent >= 60:
        label, emoji = "🥉 Бронзовый уровень", "🟠"
    else:
        label, emoji = "🌱 Ученик", "🔴"

    return {"percent": percent, "label": label, "emoji": emoji}


def build_profile_summary(user: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    total_score = int(user.get("total_score") or 0)
    rank_level, rank_title = get_rank_title(total_score)
    tasks_solved = int(user.get("tasks_solved") or 0)
    tasks_correct = int(user.get("tasks_correct") or 0)
    accuracy = get_accuracy_stats(tasks_correct, tasks_solved)

    completed_zones = set(user.get("completed_zones") or [])
    defeated_bosses = list(user.get("defeated_bosses") or [])
    inventory = list(user.get("inventory") or [])

    castle_data = user.get("castle_data") or {}
    decoration_upgrades = castle_data.get("decoration_upgrades") or {}
    if isinstance(decoration_upgrades, str):
        decoration_upgrades = {}

    return {
        "user_id": user_id,
        "first_name": user.get("first_name") or "Игрок",
        "username": user.get("username"),
        "level": user.get("level", 1),
        "xp": user.get("xp", 0),
        "xp_to_next": user.get("xp_to_next", 50),
        "rank_level": rank_level,
        "rank_title": rank_title,
        "total_score": total_score,
        "score_balance": int(user.get("score_balance") or 0),
        "tasks_solved": tasks_solved,
        "tasks_correct": tasks_correct,
        "accuracy": accuracy,
        "islands_completed": len([z for z in completed_zones if z in MAIN_ISLANDS]),
        "islands_total": len(MAIN_ISLANDS),
        "postgame_worlds_completed": len([z for z in completed_zones if z in POST_GAME_WORLDS]),
        "postgame_worlds_total": len(POST_GAME_WORLDS),
        "bosses_defeated_count": len(defeated_bosses),
        "defeated_bosses": defeated_bosses,
        "unlocked_zones": list(user.get("unlocked_zones") or ["addition"]),
        "completed_zones": list(completed_zones),
        "completed_normal_game": bool(user.get("completed_normal_game")),
        "inventory": inventory,
        "inventory_count": len(inventory),
        "artifact_upgrades": user.get("artifact_upgrades") or {},
        "achievements": user.get("achievements") or {},
        "rewards": list(user.get("rewards") or []),
        "decoration_upgrades": decoration_upgrades,
        "chaos_energy": int(user.get("chaos_energy") or 0),
        "rift_stage": int(user.get("rift_stage") or 0),
        "artifact_chaos_state": user.get("artifact_chaos_state") or "dormant",
        "consecutive_errors": int(user.get("consecutive_errors") or 0),
    }
