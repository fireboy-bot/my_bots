"""
Структурированный забег по острову — логика из handlers/levels.py для Web/ядра.
"""

import random
from typing import Any, Dict, List, Optional, Tuple

from core.progression import ISLAND_UNLOCK_CHAIN, ZONE_NAMES_RU, resolve_playable_world
from core.task_loader import get_normalized_tasks, load_world_tasks

ISLAND_TASK_COUNT = 10
WORLD_TASK_COUNT = 20

REWARD_MAP = {
    "addition": "звезда_сложения",
    "subtraction": "амулет_вычитания",
    "multiplication": "мантия_умножения",
    "division": "щит_деления",
}

BOSS_MAP = {
    "addition": "null_void",
    "subtraction": "minus_shadow",
    "multiplication": "evil_multiplier",
    "division": "fracosaur",
    "time_world": "time_keeper",
    "measure_world": "measure_keeper",
    "logic_world": "logic_keeper",
}

BOSS_NAMES = {
    "null_void": "Нуль-Пустота",
    "minus_shadow": "Минус-Тень",
    "evil_multiplier": "Злой Умножитель",
    "fracosaur": "Дробозавр",
    "time_keeper": "Хранитель Времени",
    "measure_keeper": "Хранитель Мер",
    "logic_keeper": "Хранитель Логики",
}


def _get_modifiers(user_id: str, storage) -> Dict[str, Any]:
    try:
        from handlers.effects_manager import calculate_modifiers

        return calculate_modifiers(user_id, storage) or {}
    except ImportError:
        return {}


def tasks_per_level(world_id: str) -> int:
    if world_id in ("time_world", "measure_world", "logic_world"):
        return WORLD_TASK_COUNT
    return ISLAND_TASK_COUNT


def _normalize_run_task(raw: Dict[str, Any], world_id: str, idx: int) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    if raw.get("correct_answer") is not None or raw.get("options"):
        return _normalize_task(raw, world_id, idx)
    answer = raw.get("answer", raw.get("correct_answer"))
    if answer is None:
        return None
    patched = dict(raw)
    patched["correct_answer"] = answer
    return _normalize_task(patched, world_id, idx)


def get_run_progress(user: Dict[str, Any]) -> Optional[Dict[str, int]]:
    world = user.get("current_level")
    tasks = user.get("selected_tasks") or []
    if not world or not tasks:
        return None
    idx = int(user.get("current_task_index", 0))
    total = len(tasks)
    current = min(idx + 1, total) if total else 0
    return {"current": current, "total": total, "world": world}


def get_current_run_task(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    world = user.get("current_level")
    tasks = user.get("selected_tasks") or []
    if not world or not tasks:
        return None
    idx = int(user.get("current_task_index", 0))
    if idx >= len(tasks):
        return None
    raw = tasks[idx]
    if isinstance(raw, dict) and raw.get("correct_answer") is not None and raw.get("question"):
        return dict(raw)
    return _normalize_run_task(raw, world, idx)


def start_level_run(storage, user_id: str, world_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}

    if not resolve_playable_world(user, world_id):
        return {"error": "Мир закрыт или не найден"}

    active_world = user.get("current_level")
    if active_world == world_id and user.get("selected_tasks"):
        task = get_current_run_task(user)
        if task:
            return {
                "world": world_id,
                "task": task,
                "run_progress": get_run_progress(user),
                "resumed": True,
            }

    all_tasks = get_normalized_tasks(world_id)
    if not all_tasks:
        raw = load_world_tasks(world_id)
        if not raw:
            return {"error": "Нет задач для этого мира"}
        all_tasks = get_normalized_tasks(world_id)

    count = tasks_per_level(world_id)
    selected = random.sample(all_tasks, min(count, len(all_tasks)))

    user.update(
        {
            "current_level": world_id,
            "selected_tasks": selected,
            "current_task_index": 0,
            "mistakes_in_level": 0,
            "in_boss_battle": False,
            "in_secret_level": False,
        }
    )
    storage.save_user(user_id, user)

    task = get_current_run_task(user)
    return {
        "world": world_id,
        "task": task,
        "run_progress": get_run_progress(user),
        "resumed": False,
    }


def _apply_xp_level_up(user: Dict[str, Any], xp_gain: int) -> Tuple[Dict[str, Any], Optional[int]]:
    user["xp"] = user.get("xp", 0) + xp_gain
    current_xp = user["xp"]
    player_level = user.get("level", 1)
    xp_to_next = user.get("xp_to_next", 50)
    new_player_level = None

    while current_xp >= xp_to_next:
        current_xp -= xp_to_next
        player_level += 1
        new_player_level = player_level
        xp_to_next = 50 + (player_level - 1) * 10

    user.update({"xp": current_xp, "level": player_level, "xp_to_next": xp_to_next})
    return user, new_player_level


def complete_island_level(storage, score_manager, user_id: str, user: Dict[str, Any], world_id: str) -> Dict[str, Any]:
    modifiers = _get_modifiers(user_id, storage)
    reward_item = REWARD_MAP.get(world_id)

    if reward_item:
        rewards = user.get("rewards") or []
        if reward_item not in rewards:
            rewards.append(reward_item)
        user["rewards"] = rewards

    completion_score = int(100 * modifiers.get("point_multiplier", 1.0))
    completion_xp = int(50 * modifiers.get("xp_multiplier", 1.0))

    if modifiers.get("perfect_run_bonus", 0) > 0 and user.get("mistakes_in_level", 0) == 0:
        completion_score += int(modifiers.get("perfect_run_bonus", 0))

    if score_manager and completion_score > 0:
        score_manager.add_score(
            user_id=user_id,
            amount=completion_score,
            reason="level_complete",
            context=f"level_{world_id}",
        )
        refreshed = storage.get_user(user_id)
        if refreshed:
            user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))
            user["total_score"] = refreshed.get("total_score", user.get("total_score", 0))

    user, player_level_up = _apply_xp_level_up(user, completion_xp)

    completed = set(user.get("completed_zones") or [])
    completed.add(world_id)
    user["completed_zones"] = list(completed)

    boss_id = BOSS_MAP.get(world_id)
    defeated = set(user.get("defeated_bosses") or [])
    boss_pending = None
    unlocked_zone = None

    if boss_id and boss_id not in defeated:
        boss_pending = {"id": boss_id, "name": BOSS_NAMES.get(boss_id, boss_id)}
        user["just_completed_level"] = world_id
    else:
        user["just_completed_level"] = None
        next_zone = ISLAND_UNLOCK_CHAIN.get(world_id)
        if next_zone:
            unlocked = list(user.get("unlocked_zones") or ["addition"])
            if next_zone not in unlocked:
                unlocked.append(next_zone)
                user["unlocked_zones"] = unlocked
                unlocked_zone = next_zone

    user["current_level"] = None
    user["selected_tasks"] = []
    user["current_task_index"] = 0
    user["mistakes_in_level"] = 0

    storage.save_user(user_id, user)

    zone_name = ZONE_NAMES_RU.get(world_id, world_id)
    place_word = "Мир" if world_id in ("time_world", "measure_world", "logic_world") else "Остров"
    next_name = ZONE_NAMES_RU.get(unlocked_zone, unlocked_zone) if unlocked_zone else None
    if unlocked_zone:
        message = f"🏆 {place_word} «{zone_name}» пройден! 🔓 Открыт: {next_name}"
    elif boss_pending:
        message = f"🏆 {place_word} «{zone_name}» пройден! ⚔️ Время бить босса: {boss_pending['name']}"
    else:
        message = f"🏆 {place_word} «{zone_name}» пройден!"

    return {
        "island_complete": True,
        "completed_zone": world_id,
        "unlocked_zone": unlocked_zone,
        "reward_item": reward_item,
        "completion_bonus": completion_score,
        "boss_pending": boss_pending,
        "player_level_up": player_level_up,
        "message": message,
    }


def process_level_answer(
    storage,
    score_manager,
    user_id: str,
    is_correct: bool,
) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}

    world_id = user.get("current_level")
    tasks: List[Dict[str, Any]] = user.get("selected_tasks") or []
    task_idx = int(user.get("current_task_index", 0))

    if not world_id or not tasks or task_idx >= len(tasks):
        return {"error": "Нет активного забега"}

    user["tasks_solved"] = user.get("tasks_solved", 0) + 1
    if is_correct:
        user["tasks_correct"] = user.get("tasks_correct", 0) + 1

    if not is_correct:
        modifiers = _get_modifiers(user_id, storage)
        penalty = 15
        refund_ratio = modifiers.get("penalty_refund_ratio", 0.0)
        if refund_ratio > 0:
            penalty = int(penalty * (1 - refund_ratio))
        if modifiers.get("mistake_penalty_ignored", False):
            penalty = 0
        elif modifiers.get("ignore_first_mistake", False) and user.get("mistakes_in_level", 0) == 0:
            penalty = 0

        if penalty > 0 and score_manager:
            score_manager.spend_score(
                user_id=user_id,
                amount=penalty,
                reason="level_task_wrong",
                context=f"level_{world_id}_task_{task_idx}",
            )
            refreshed = storage.get_user(user_id)
            if refreshed:
                user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))

        user["xp"] = max(0, user.get("xp", 0) - 5)
        user["mistakes_in_level"] = user.get("mistakes_in_level", 0) + 1
        storage.save_user(user_id, user)

        return {
            "correct": False,
            "reward": -penalty if penalty > 0 else 0,
            "message": "❌ Неверно! Попробуй ещё раз",
            "run_progress": get_run_progress(user),
            "island_complete": False,
            "retry_same_task": True,
            "new_balance": user.get("score_balance", 0),
            "new_total_score": user.get("total_score", 0),
        }

    modifiers = _get_modifiers(user_id, storage)
    earned_score = int(50 * modifiers.get("point_multiplier", 1.0))

    if score_manager:
        score_manager.add_score(
            user_id=user_id,
            amount=earned_score,
            reason="level_task_correct",
            context=f"level_{world_id}_task_{task_idx}",
        )
        refreshed = storage.get_user(user_id)
        if refreshed:
            user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))
            user["total_score"] = refreshed.get("total_score", user.get("total_score", 0))

    earned_xp = int((10 + modifiers.get("xp_bonus_per_task", 0)) * modifiers.get("xp_multiplier", 1.0))
    user, player_level_up = _apply_xp_level_up(user, earned_xp)

    user["current_task_index"] = task_idx + 1
    storage.save_user(user_id, user)

    if task_idx + 1 >= len(tasks):
        completion = complete_island_level(storage, score_manager, user_id, user, world_id)
        user = storage.get_user(user_id) or user
        return {
            "correct": True,
            "reward": earned_score,
            "message": completion["message"],
            "run_progress": None,
            "island_complete": True,
            "completed_zone": completion["completed_zone"],
            "unlocked_zone": completion["unlocked_zone"],
            "reward_item": completion.get("reward_item"),
            "completion_bonus": completion.get("completion_bonus"),
            "boss_pending": completion.get("boss_pending"),
            "player_level_up": completion.get("player_level_up") or player_level_up,
            "new_balance": user.get("score_balance", 0),
            "new_total_score": user.get("total_score", 0),
        }

    next_task = get_current_run_task(user)
    progress = get_run_progress(user)
    return {
        "correct": True,
        "reward": earned_score,
        "message": "✅ Верно!",
        "run_progress": progress,
        "island_complete": False,
        "next_task": next_task,
        "player_level_up": player_level_up,
        "new_balance": user.get("score_balance", 0),
        "new_total_score": user.get("total_score", 0),
    }
