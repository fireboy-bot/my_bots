"""
Бои с боссами — синхронная логика для Web (по мотивам handlers/bosses.py).
"""

import json
import os
import random
from typing import Any, Dict, List, Optional

from config import BOSS_DATA_DIR, BOSSES_INFO_FILE
from core.level_run import BOSS_MAP, BOSS_NAMES

ISLAND_BOSS_MAP = BOSS_MAP

REWARD_MAP = {
    "null_void": "звезда_сложения",
    "minus_shadow": "амулет_вычитания",
    "evil_multiplier": "мантия_умножения",
    "fracosaur": "щит_деления",
    "final_boss": "корона_матемага",
}

_BOSS_INFO: Optional[Dict[str, Any]] = None


def _load_boss_info() -> Dict[str, Any]:
    global _BOSS_INFO
    if _BOSS_INFO is None:
        try:
            with open(BOSSES_INFO_FILE, "r", encoding="utf-8") as f:
                _BOSS_INFO = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _BOSS_INFO = {}
    return _BOSS_INFO


def _get_modifiers(user_id: str, storage) -> Dict[str, Any]:
    try:
        from handlers.effects_manager import calculate_modifiers

        return calculate_modifiers(user_id, storage) or {}
    except ImportError:
        return {}


def load_boss_tasks(boss_id: str) -> Optional[List[Dict[str, Any]]]:
    if boss_id == "true_lord":
        return None
    boss_file = os.path.join(BOSS_DATA_DIR, f"{boss_id}.json")
    try:
        with open(boss_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        return tasks if isinstance(tasks, list) else None
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_boss_reward(boss_id: str) -> str:
    return REWARD_MAP.get(boss_id, "звезда_сложения")


def unlock_new_zones(progress: Dict[str, Any], boss_id: str) -> Dict[str, Any]:
    unlocked = set(progress.get("unlocked_zones", ["addition"]))

    if boss_id == "null_void":
        unlocked.add("subtraction")
    elif boss_id == "minus_shadow":
        unlocked.add("multiplication")
    elif boss_id == "evil_multiplier":
        unlocked.add("division")
    elif boss_id == "fracosaur":
        unlocked.add("secret_level")
    elif boss_id == "final_boss":
        unlocked.update({"time_world", "measure_world", "logic_world", "true_lord"})
        progress["completed_normal_game"] = True

    progress["unlocked_zones"] = list(unlocked)

    zone_map = {
        "null_void": "addition",
        "minus_shadow": "subtraction",
        "evil_multiplier": "multiplication",
        "fracosaur": "division",
        "time_keeper": "time_world",
        "measure_keeper": "measure_world",
        "logic_keeper": "logic_world",
    }
    zone_id = zone_map.get(boss_id)
    if zone_id:
        completed = set(progress.get("completed_zones") or [])
        completed.add(zone_id)
        completed.add(f"boss_{boss_id}")
        progress["completed_zones"] = list(completed)

    return progress


def check_ability_trigger(ability: Dict[str, Any], is_correct: bool, boss_health: int, task_idx: int, total_tasks: int) -> bool:
    trigger = ability.get("trigger", "")
    if trigger == "при ошибке":
        return not is_correct
    if trigger == "каждый ход":
        return True
    if trigger == "когда HP ≤ 2":
        return boss_health <= 2
    if trigger == "когда HP ≤ 3":
        return boss_health <= 3
    if trigger == "за каждые 2 решённые задачи":
        return (task_idx + 1) % 2 == 0
    return False


def _apply_boss_ability_sync(
    user_id: str,
    boss_id: str,
    ability: Dict[str, Any],
    progress: Dict[str, Any],
    is_correct: bool,
    score_manager,
) -> Optional[str]:
    effect = ability.get("effect", "")
    boss_health = progress.get("boss_health", 5)
    max_health = 10 if boss_id == "true_lord" else 5
    current_balance = progress.get("score_balance", 0)
    used = progress.get("boss_abilities_used") or []
    name = ability.get("name", "Способность")

    if "восстанавливает 1 HP" in effect:
        progress["boss_health"] = min(max_health, boss_health + 1)
        used.append(name)
    elif "удваивает текущее HP" in effect and boss_health <= 2:
        progress["boss_health"] = min(max_health, boss_health * 2)
        used.append(name)
    elif "крадёт 5 очков" in effect and not is_correct:
        if score_manager:
            score_manager.spend_score(user_id, 5, "boss_ability", f"{boss_id}_steal_5")
        else:
            progress["score_balance"] = max(0, current_balance - 5)
        used.append(name)
    elif "крадёт до 10 очков" in effect and not is_correct:
        stolen = min(10, current_balance)
        if score_manager and stolen > 0:
            score_manager.spend_score(user_id, stolen, "boss_ability", f"{boss_id}_steal_up_to_10")
        progress["boss_health"] = min(max_health, boss_health + 1)
        used.append(name)

    progress["boss_abilities_used"] = used
    return name if name in used else None


def _normalize_boss_task(raw: Dict[str, Any], boss_id: str, idx: int) -> Dict[str, Any]:
    answer = raw.get("answer", raw.get("correct_answer"))
    return {
        "id": raw.get("id") or f"boss_{boss_id}_{idx}",
        "question": raw.get("question", ""),
        "correct_answer": str(answer).strip(),
        "hint": raw.get("hint", ""),
        "island": boss_id,
        "operation_type": "boss",
    }


def get_boss_max_health(boss_id: str) -> int:
    return 10 if boss_id == "true_lord" else 5


def get_boss_state(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not user.get("in_boss_battle"):
        return None
    boss_id = user.get("current_boss")
    if not boss_id:
        return None

    tasks = user.get("selected_boss_tasks") or []
    idx = int(user.get("boss_task_index", 0))
    info = _load_boss_info().get(boss_id, {})
    max_hp = get_boss_max_health(boss_id)
    hp = int(user.get("boss_health", max_hp))

    task = None
    if idx < len(tasks):
        task = _normalize_boss_task(tasks[idx], boss_id, idx)

    return {
        "boss_id": boss_id,
        "boss_name": info.get("name", BOSS_NAMES.get(boss_id, boss_id)),
        "boss_emoji": info.get("emoji", "👹"),
        "boss_description": info.get("description", ""),
        "boss_health": hp,
        "boss_max_health": max_hp,
        "task_index": idx + 1 if task else idx,
        "total_tasks": len(tasks),
        "task": task,
    }


def resolve_boss_id(user: Dict[str, Any], boss_id: Optional[str]) -> Optional[str]:
    if boss_id:
        return boss_id
    completed = user.get("just_completed_level")
    if completed:
        return ISLAND_BOSS_MAP.get(completed)
    return None


def start_boss_run(storage, user_id: str, boss_id: Optional[str] = None) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}

    boss_id = resolve_boss_id(user, boss_id)
    if not boss_id:
        return {"error": "Босс не указан"}

    defeated = set(user.get("defeated_bosses") or [])
    if boss_id in defeated:
        return {"error": "Этот босс уже побеждён"}

    if user.get("in_boss_battle") and user.get("current_boss") == boss_id:
        state = get_boss_state(user)
        if state and state.get("task"):
            return {**state, "resumed": True}

    tasks = load_boss_tasks(boss_id)
    if not tasks:
        return {"error": f"Задачи для босса '{boss_id}' не найдены"}

    selected = tasks.copy()
    random.shuffle(selected)
    max_hp = get_boss_max_health(boss_id)

    user.update(
        {
            "in_boss_battle": True,
            "current_boss": boss_id,
            "selected_boss_tasks": selected,
            "boss_task_index": 0,
            "boss_health": max_hp,
            "boss_max_health": max_hp,
            "boss_abilities_used": [],
            "boss_turn": 0,
            "current_level": None,
            "selected_tasks": [],
            "current_task_index": 0,
        }
    )
    storage.save_user(user_id, user)

    state = get_boss_state(user)
    info = _load_boss_info().get(boss_id, {})
    return {
        **(state or {}),
        "resumed": False,
        "intro": info.get("description", ""),
    }


def exit_boss_run(storage, user_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user or not user.get("in_boss_battle"):
        return {"success": True, "message": "Бой не активен"}

    boss_id = user.get("current_boss")
    max_hp = get_boss_max_health(boss_id or "")
    user.update(
        {
            "in_boss_battle": False,
            "current_boss": None,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "boss_health": max_hp,
            "boss_abilities_used": [],
        }
    )
    storage.save_user(user_id, user)
    return {"success": True, "message": "↩️ Вышла из боя"}


def process_boss_answer(storage, score_manager, user_id: str, answer: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user or not user.get("in_boss_battle"):
        return {"error": "Нет активного боя с боссом"}

    boss_id = user.get("current_boss")
    if not boss_id:
        return {"error": "Босс не найден"}

    tasks = user.get("selected_boss_tasks") or []
    task_idx = int(user.get("boss_task_index", 0))
    boss_health = int(user.get("boss_health", 5))
    max_hp = get_boss_max_health(boss_id)

    if task_idx >= len(tasks) and boss_health > 0:
        random.shuffle(tasks)
        user["selected_boss_tasks"] = tasks
        user["boss_task_index"] = 0
        task_idx = 0
        storage.save_user(user_id, user)

    if task_idx >= len(tasks):
        return {"error": "Нет задач босса"}

    current = tasks[task_idx]
    try:
        given = float(str(answer).strip().replace(",", "."))
        expected = float(current["answer"])
        is_correct = abs(given - expected) < 0.01
    except (ValueError, TypeError, KeyError):
        return {"correct": False, "message": "🔢 Нужно ввести число", "retry_same_task": True}

    user["tasks_solved"] = user.get("tasks_solved", 0) + 1
    if is_correct:
        user["tasks_correct"] = user.get("tasks_correct", 0) + 1

    ability_triggered = None
    boss_info = _load_boss_info().get(boss_id, {})
    for ability in boss_info.get("abilities", []):
        chance_str = str(ability.get("chance", "0")).replace("%", "")
        try:
            chance = int(chance_str)
        except ValueError:
            chance = 0
        if check_ability_trigger(ability, is_correct, boss_health, task_idx, len(tasks)):
            if random.randint(1, 100) <= chance:
                triggered = _apply_boss_ability_sync(user_id, boss_id, ability, user, is_correct, score_manager)
                if triggered:
                    ability_triggered = {"name": triggered, "effect": ability.get("effect", "")}
                boss_health = int(user.get("boss_health", boss_health))
                break

    modifiers = _get_modifiers(user_id, storage)
    reward = 0

    if is_correct:
        points = int(20 * modifiers.get("point_multiplier", 1.0)) + modifiers.get("boss_win_bonus_points", 0)
        if score_manager:
            score_manager.add_score(user_id, points, "boss_task_correct", f"boss_{boss_id}_task_{task_idx}")
        else:
            user["score_balance"] = user.get("score_balance", 0) + points
            user["total_score"] = user.get("total_score", 0) + points
        reward = points
        user["boss_health"] = max(0, boss_health - 1)
        user["boss_task_index"] = task_idx + 1
        message = "✅ Удар по боссу!"
    else:
        penalty = 15
        if not modifiers.get("mistake_penalty_ignored", False):
            if score_manager:
                score_manager.spend_score(user_id, penalty, "boss_task_wrong", f"boss_{boss_id}_task_{task_idx}")
            else:
                user["score_balance"] = max(0, user.get("score_balance", 0) - penalty)
            reward = -penalty
        user["boss_task_index"] = task_idx + 1
        message = "❌ Промах! Босс держится"

    refreshed = storage.get_user(user_id)
    if refreshed:
        user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))
        user["total_score"] = refreshed.get("total_score", user.get("total_score", 0))

    storage.save_user(user_id, user)

    if user["boss_health"] <= 0:
        return _finalize_boss_victory(storage, user_id, user, boss_id)

    new_idx = int(user.get("boss_task_index", 0))
    if new_idx >= len(tasks):
        exit_boss_run(storage, user_id)
        return {
            "correct": is_correct,
            "reward": reward,
            "message": "❗ Босс слишком силён! Попробуй позже.",
            "boss_failed": True,
            "new_balance": user.get("score_balance", 0),
        }

    next_task = _normalize_boss_task(tasks[new_idx], boss_id, new_idx)
    hp = int(user.get("boss_health", 0))
    return {
        "correct": is_correct,
        "reward": reward,
        "message": message,
        "boss_health": hp,
        "boss_max_health": max_hp,
        "task_index": new_idx + 1,
        "total_tasks": len(tasks),
        "next_task": next_task,
        "ability_triggered": ability_triggered,
        "boss_defeated": False,
        "new_balance": user.get("score_balance", 0),
        "new_total_score": user.get("total_score", 0),
    }


def _finalize_boss_victory(storage, user_id: str, user: Dict[str, Any], boss_id: str) -> Dict[str, Any]:
    reward_item = get_boss_reward(boss_id)
    rewards = user.get("rewards") or []
    if reward_item not in rewards:
        rewards.append(reward_item)
    user["rewards"] = rewards

    defeated = list(user.get("defeated_bosses") or [])
    newly_defeated = boss_id not in defeated
    if newly_defeated:
        defeated.append(boss_id)
        user["defeated_bosses"] = defeated
        user = unlock_new_zones(user, boss_id)

    user.update(
        {
            "in_boss_battle": False,
            "current_boss": None,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "just_completed_level": None,
            "current_level": None,
            "selected_tasks": [],
            "current_task_index": 0,
        }
    )
    storage.save_user(user_id, user)

    info = _load_boss_info().get(boss_id, {})
    name = info.get("name", BOSS_NAMES.get(boss_id, boss_id))
    unlocked = user.get("unlocked_zones", [])

    return {
        "correct": True,
        "boss_defeated": True,
        "reward_item": reward_item,
        "unlocked_zones": unlocked,
        "message": f"🎉 ПОБЕДА над {name}! Награда: {reward_item.replace('_', ' ')}",
        "boss_health": 0,
        "new_balance": user.get("score_balance", 0),
        "new_total_score": user.get("total_score", 0),
    }
