"""
Тайная комната — логика для Web (без Telegram).
Порт handlers/secret_room.py → ядро.
"""

import json
import os
import random
import logging
from typing import Any, Dict, List, Optional, Tuple

from core.vladimir_profile import PlayerProfile
from core.boss_run import is_castle_unlocked

logger = logging.getLogger(__name__)

SECRET_ROOM_MAX_ATTEMPTS = 3
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SECRET_ITEMS = {
    "ancient_coin": "🪙 Древняя монета",
    "crystal_shard": "💎 Осколок кристалла",
    "logic_key": "🗝️ Ключ логики",
    "wisdom_scroll": "📜 Свиток мудрости",
}

LORE_ENTRIES = [
    "📜 Дневник Архитектора: «Сегодня я заложил первый камень Числяндии.»",
    "📜 Запись в фолианте: «Тот, кто постигнет сложение, откроет врата.»",
    "📜 Письмо игрока: «Я думал, что 7×8=54... Владимир был недоволен.»",
    "📜 Легенда о Финальном Владыке: «Порядок рождается из понимания, а не из страха.»",
    "📜 Заметка Манюни: «Ошибка — это шаг к правильному ответу.»",
]

EVENT_WEIGHTS = {
    "puzzle": 40,
    "reward": 30,
    "lore": 20,
    "empty": 10,
}

_PUZZLES_CACHE: Optional[List[dict]] = None


def _load_puzzles() -> List[dict]:
    global _PUZZLES_CACHE
    if _PUZZLES_CACHE is not None:
        return _PUZZLES_CACHE

    tasks_file = os.path.join(DATA_DIR, "secret_room_tasks.json")
    if not os.path.exists(tasks_file):
        _PUZZLES_CACHE = [
            {
                "id": "p1",
                "question": "Сколько будет 7 × 8?",
                "options": ["54", "56", "64"],
                "correct": 1,
                "reward_points": 20,
                "reward_item": None,
                "explanation": "7 × 8 = 56",
            },
        ]
        return _PUZZLES_CACHE

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_tasks = []
        for category in data.values():
            for task in category:
                all_tasks.append(
                    {
                        "id": f"t{len(all_tasks) + 1}",
                        "question": task["question"],
                        "options": [str(o) for o in task["options"]],
                        "correct": task["correct"],
                        "reward_points": task.get("reward", 10),
                        "reward_item": None,
                        "explanation": task.get("explanation", ""),
                    }
                )
        _PUZZLES_CACHE = all_tasks
    except Exception as exc:
        logger.error("secret_room puzzles load error: %s", exc)
        _PUZZLES_CACHE = []

    return _PUZZLES_CACHE


def _load_lore_entries() -> List[dict]:
    lore_file = os.path.join(DATA_DIR, "secret_lore.json")
    if not os.path.exists(lore_file):
        return []
    try:
        with open(lore_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("lore_entries", [])
    except Exception:
        return []


def _get_room_progress(user: Dict[str, Any]) -> Dict[str, Any]:
    profile = user.get("player_profile") or {}
    secret = profile.get("secret_room") or {}
    return {
        "level": secret.get("room_level", user.get("secret_room_level", 1)),
        "exp": secret.get("room_exp", user.get("secret_room_exp", 0)),
        "items": list(secret.get("room_items", user.get("secret_room_items", []))),
        "logs": list(secret.get("room_logs", user.get("secret_room_logs", []))),
        "last_event": secret.get("room_last_event", user.get("secret_room_last_event")),
    }


def _save_room_progress(user: Dict[str, Any], progress: Dict[str, Any]) -> None:
    profile = dict(user.get("player_profile") or {})
    secret = dict(profile.get("secret_room") or {})
    secret["room_level"] = progress.get("level", 1)
    secret["room_exp"] = progress.get("exp", 0)
    secret["room_items"] = progress.get("items", [])
    secret["room_logs"] = progress.get("logs", [])
    secret["room_last_event"] = progress.get("last_event")
    profile["secret_room"] = secret
    user["player_profile"] = profile
    user["secret_room_level"] = secret["room_level"]
    user["secret_room_exp"] = secret["room_exp"]
    user["secret_room_items"] = secret["room_items"]
    user["secret_room_logs"] = secret["room_logs"]
    user["secret_room_last_event"] = secret["room_last_event"]


def _exp_for_next_level(level: int) -> int:
    return 50 * (2 ** (level - 1))


def _check_level_up(progress: Dict[str, Any]) -> Tuple[bool, str]:
    current_level = progress.get("level", 1)
    current_exp = progress.get("exp", 0)
    exp_needed = _exp_for_next_level(current_level)
    if current_exp >= exp_needed:
        progress["level"] = current_level + 1
        progress["exp"] = 0
        next_exp = _exp_for_next_level(progress["level"])
        return True, f"🎉 Уровень тайной комнаты: {progress['level']}! Опыт: 0/{next_exp}"
    return False, ""


def _add_reward(
    user: Dict[str, Any],
    progress: Dict[str, Any],
    points: int,
    item: Optional[str] = None,
    score_manager=None,
    user_id: Optional[str] = None,
) -> Tuple[str, bool, str]:
    messages = []
    if points > 0:
        if score_manager and user_id:
            score_manager.add_score(user_id, points, "secret_room", "reward")
            refreshed = score_manager.storage.get_user(user_id)
            if refreshed:
                user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))
                user["total_score"] = refreshed.get("total_score", user.get("total_score", 0))
        else:
            user["score_balance"] = user.get("score_balance", 0) + points
            user["total_score"] = user.get("total_score", 0) + points
        progress["exp"] = progress.get("exp", 0) + points
        messages.append(f"✨ +{points} очков!")

    if item and item not in progress.get("items", []):
        progress.setdefault("items", []).append(item)
        messages.append(f"🎁 {SECRET_ITEMS.get(item, item)}")

    leveled_up, level_message = _check_level_up(progress)
    if leveled_up:
        messages.append(level_message)

    return " ".join(messages), leveled_up, level_message


def _roll_event() -> str:
    events = list(EVENT_WEIGHTS.keys())
    weights = list(EVENT_WEIGHTS.values())
    return random.choices(events, weights=weights, k=1)[0]


def _build_state(user: Dict[str, Any]) -> Dict[str, Any]:
    profile = PlayerProfile(user)
    status = profile.get_secret_room_status()
    progress = _get_room_progress(user)
    completion = profile.get_lore_completion()
    exp_needed = _exp_for_next_level(progress["level"])

    return {
        "unlocked": is_castle_unlocked(user),
        "available": status["available"] and is_castle_unlocked(user),
        "attempts_left": status["attempts_left"],
        "attempts_max": SECRET_ROOM_MAX_ATTEMPTS,
        "resets_at": status["resets_at"],
        "streak": status["streak"],
        "total_visits": status["total_visits"],
        "level": progress["level"],
        "exp": progress["exp"],
        "exp_needed": exp_needed,
        "items": [
            {"id": item_id, "name": SECRET_ITEMS.get(item_id, item_id)}
            for item_id in progress["items"]
        ],
        "logs_count": len(progress["logs"]),
        "logs_preview": progress["logs"][-3:],
        "lore_completion": completion,
    }


def get_secret_room_state(storage, user_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}
    return _build_state(user)


def explore_secret_room(storage, score_manager, user_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}

    if not is_castle_unlocked(user):
        return {"success": False, "message": "🔒 Тайная комната откроется после победы над Финальным Владыкой!"}

    profile = PlayerProfile(user)
    status = profile.get_secret_room_status()
    if status["attempts_left"] <= 0:
        return {
            "success": False,
            "message": f"⚠️ Попытки на сегодня исчерпаны. Откроется через: {status['resets_at']}",
            "state": _build_state(user),
        }

    progress = _get_room_progress(user)
    event_type = _roll_event()
    progress["last_event"] = event_type
    lore_seen: List[str] = []
    result: Dict[str, Any] = {"success": True, "event_type": event_type}

    if event_type == "puzzle":
        puzzles = _load_puzzles()
        if not puzzles:
            event_type = "empty"
            result["event_type"] = "empty"
        else:
            puzzle = random.choice(puzzles)
            result.update(
                {
                    "title": "🧩 Загадка",
                    "message": puzzle["question"],
                    "puzzle": {
                        "id": puzzle["id"],
                        "question": puzzle["question"],
                        "options": puzzle["options"],
                    },
                }
            )
    elif event_type == "reward":
        points = random.choice([10, 15, 20])
        reward_text, leveled_up, level_message = _add_reward(
            user, progress, points, score_manager=score_manager, user_id=user_id
        )
        result.update(
            {
                "title": "✨ Находка!",
                "message": f"{reward_text}",
                "level_up": leveled_up,
                "level_message": level_message,
            }
        )
    elif event_type == "lore":
        all_lore = _load_lore_entries()
        lore_text = random.choice(LORE_ENTRIES)
        if all_lore:
            seen = set(profile.profile.get("secret_room", {}).get("lore_seen", []))
            available = [entry for entry in all_lore if entry.get("id") not in seen]
            if available:
                entry = random.choice(available)
                lore_seen.append(entry["id"])
                lore_text = f"📜 {entry.get('title', 'Запись')}\n\n{entry.get('text', '')}"
        if lore_text not in progress["logs"]:
            progress["logs"].append(lore_text)
        completion = profile.get_lore_completion()
        result.update(
            {
                "title": "📜 Запись в дневнике",
                "message": lore_text,
                "lore_completion": completion,
            }
        )
    else:
        empty_messages = [
            "🔍 Ты осмотрелась... пока ничего интересного.",
            "🕯️ Пыль и тишина. Попробуй ещё раз!",
            "🗝️ Комната хранит секреты.",
            "✨ Что-то шевельнулось... но исчезло.",
        ]
        result.update(
            {
                "title": "🔍 Исследование",
                "message": random.choice(empty_messages),
            }
        )

    profile.track_secret_room_visit(lore_seen=lore_seen)
    _save_room_progress(user, progress)
    storage.save_user(user_id, user)
    result["state"] = _build_state(user)
    return result


def answer_secret_puzzle(
    storage,
    score_manager,
    user_id: str,
    puzzle_id: str,
    option_index: int,
) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}

    puzzle = next((p for p in _load_puzzles() if p["id"] == puzzle_id), None)
    if not puzzle:
        return {"success": False, "message": "❌ Загадка не найдена"}

    progress = _get_room_progress(user)
    is_correct = option_index == puzzle["correct"]

    if is_correct:
        reward_text, leveled_up, level_message = _add_reward(
            user,
            progress,
            puzzle.get("reward_points", 10),
            puzzle.get("reward_item"),
            score_manager=score_manager,
            user_id=user_id,
        )
        message = f"✅ Правильно!\n\n{puzzle.get('explanation', '')}\n\n{reward_text}"
    else:
        correct_option = puzzle["options"][puzzle["correct"]]
        progress["exp"] = progress.get("exp", 0) + 1
        message = f"❌ Не совсем...\n\nПравильный ответ: {correct_option}\n💡 {puzzle.get('explanation', '')}"
        leveled_up, level_message = False, ""

    _save_room_progress(user, progress)
    storage.save_user(user_id, user)

    return {
        "success": True,
        "correct": is_correct,
        "message": message,
        "level_up": leveled_up if is_correct else False,
        "level_message": level_message if is_correct else "",
        "state": _build_state(user),
    }
