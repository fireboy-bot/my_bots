"""
Загрузка задач — единый источник для TG, Web и ядра.
Источник: data/worlds/{world_id}.json (как handlers/levels.py).
"""

import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from config import WORLD_DATA_DIR

logger = logging.getLogger(__name__)


def load_world_tasks(world_id: str) -> List[Dict[str, Any]]:
    """Сырые задачи мира — тот же формат, что читает Telegram."""
    world_file = os.path.join(WORLD_DATA_DIR, f"{world_id}.json")
    if not os.path.exists(world_file):
        logger.warning(f"[task_loader] Файл мира не найден: {world_file}")
        return []
    try:
        with open(world_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        return tasks if isinstance(tasks, list) else []
    except Exception as e:
        logger.error(f"[task_loader] Ошибка чтения {world_file}: {e}")
        return []


def _detect_operation_type(question: str) -> str:
    q = (question or "").lower()
    if "×" in q or "*" in q or "умнож" in q:
        return "1digit_mult"
    if "÷" in q or "/" in q or "дел" in q:
        return "2digit_div"
    if "-" in q or "вычит" in q:
        return "2digit_sub"
    return "2digit_add"


def _normalize_task(raw: Dict[str, Any], world_name: str, idx: int) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    correct = raw.get("correct_answer", raw.get("answer"))
    if correct is None:
        return None
    correct_str = str(correct).strip()

    options = raw.get("options")
    if not options or not isinstance(options, list):
        try:
            c = int(correct_str)
            opts = {correct_str}
            for off in (-10, -5, -3, 3, 5, 10):
                w = str(c + off)
                if w != correct_str:
                    opts.add(w)
                if len(opts) >= 4:
                    break
            options = list(opts)
            random.shuffle(options)
        except (ValueError, TypeError):
            options = [correct_str] * 4

    return {
        "id": raw.get("id") or f"{world_name}_{idx}",
        "question": raw.get("question", ""),
        "correct_answer": correct_str,
        "options": options,
        "score": raw.get("score", 10),
        "world": world_name,
        "island": world_name,
        "operation_type": raw.get("operation_type") or _detect_operation_type(raw.get("question", "")),
        "hint": raw.get("hint", ""),
    }


def get_normalized_tasks(world_id: str) -> List[Dict[str, Any]]:
    """Нормализованные задачи для web/API."""
    raw_tasks = load_world_tasks(world_id)
    result = []
    for idx, raw in enumerate(raw_tasks):
        task = _normalize_task(raw, world_id, idx)
        if task:
            result.append(task)
    return result


def parse_task_id(task_id: str) -> tuple[Optional[str], Optional[int]]:
    """addition_11 → ('addition', 11)"""
    if not task_id or "_" not in task_id:
        return None, None
    world, idx_str = task_id.rsplit("_", 1)
    if idx_str.isdigit():
        return world, int(idx_str)
    return None, None


def resolve_expected_answer(task_id: str, island_id: Optional[str] = None, client_expected: Any = None) -> Optional[str]:
    """Правильный ответ по task_id из файлов миров."""
    if not task_id:
        if client_expected is None:
            return None
        return str(client_expected).strip().replace(",", ".")

    lookup_id = str(task_id)
    if lookup_id.startswith("transfer_"):
        lookup_id = lookup_id[len("transfer_") :]

    world, _ = parse_task_id(lookup_id)
    search_world = island_id or world
    if search_world:
        for task in get_normalized_tasks(search_world):
            if task.get("id") == lookup_id:
                return str(task.get("correct_answer", "")).strip()

    if client_expected is not None:
        return str(client_expected).strip().replace(",", ".")
    return None


def pick_random_task(world_id: str) -> Optional[Dict[str, Any]]:
    tasks = get_normalized_tasks(world_id)
    return random.choice(tasks) if tasks else None


def pick_task_for_user(storage, user_id: str, world: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Выбор задачи с учётом прогресса игрока (как в TG — по разблокированным мирам)."""
    if not world:
        user = storage.get_user(user_id) if storage else None
        zones = (user or {}).get("unlocked_zones") or ["addition"]
        world = zones[-1] if zones else "addition"
    return pick_random_task(world)
