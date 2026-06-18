"""
Общие утилиты боёв с боссами (boss_run + true_lord_run).
"""

from typing import Any, Dict, Optional, Tuple

BATTLE_PAYLOAD_KEYS = (
    "boss_health",
    "boss_max_health",
    "task_index",
    "total_tasks",
    "next_task",
    "retry_same_task",
    "boss_defeated",
    "boss_failed",
    "ability_triggered",
    "phase",
    "phase_name",
    "avatar_url",
    "phase_changed",
    "dialogues",
    "boss_id",
    "absolute_victory",
    "reward_item",
    "unlocked_zones",
    "castle_unlocked",
    "completed_normal_game",
    "victory_bonus",
    "finale_text",
    "secret_text",
    "epic",
)

INVALID_NUMERIC_ANSWER = "🔢 Нужно ввести число"


def get_modifiers(user_id: str, storage) -> Dict[str, Any]:
    try:
        from handlers.effects_manager import calculate_modifiers

        return calculate_modifiers(user_id, storage) or {}
    except ImportError:
        return {}


def normalize_boss_task(raw: Dict[str, Any], boss_id: str, idx: int) -> Dict[str, Any]:
    answer = raw.get("answer", raw.get("correct_answer"))
    task_id = raw.get("id")
    if not task_id:
        task_id = f"true_lord_{idx}" if boss_id == "true_lord" else f"boss_{boss_id}_{idx}"
    return {
        "id": task_id,
        "question": raw.get("question", ""),
        "correct_answer": str(answer).strip(),
        "hint": raw.get("hint", ""),
        "island": boss_id,
        "operation_type": "boss",
    }


def parse_numeric_answer(answer: str, expected_raw: Any) -> Tuple[Optional[bool], Optional[str]]:
    """
    Возвращает (is_correct, invalid_message).
    invalid_message задан — ответ не числовой.
    """
    try:
        given = float(str(answer).strip().replace(",", "."))
        expected = float(expected_raw)
        return abs(given - expected) < 0.01, None
    except (ValueError, TypeError, KeyError):
        return None, INVALID_NUMERIC_ANSWER


def invalid_numeric_response() -> Dict[str, Any]:
    return {"correct": False, "message": INVALID_NUMERIC_ANSWER, "retry_same_task": True}


def refresh_user_scores(storage, user_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    refreshed = storage.get_user(user_id)
    if refreshed:
        user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))
        user["total_score"] = refreshed.get("total_score", user.get("total_score", 0))
    return user


def infer_battle_mode(user: Optional[Dict[str, Any]], result: Dict[str, Any]) -> Optional[str]:
    current_boss = (user or {}).get("current_boss") or result.get("boss_id")
    if current_boss == "true_lord" and (user or {}).get("true_lord_epic"):
        return "true_lord"
    if result.get("absolute_victory") or result.get("epic"):
        return "true_lord"
    battle_keys = (
        "boss_health",
        "boss_defeated",
        "boss_failed",
        "next_task",
        "retry_same_task",
        "phase",
    )
    if any(key in result for key in battle_keys):
        if current_boss == "true_lord":
            return "true_lord"
        return "boss"
    if user and user.get("in_boss_battle"):
        if user.get("current_boss") == "true_lord" and user.get("true_lord_epic"):
            return "true_lord"
        return "boss"
    return None


def build_battle_block(result: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    mode = infer_battle_mode(user, result)
    if not mode:
        return None
    battle: Dict[str, Any] = {"mode": mode}
    for key in BATTLE_PAYLOAD_KEYS:
        if key in result:
            battle[key] = result[key]
    return battle


def enrich_game_response(result: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if result.get("error"):
        return {**result, "ok": False}

    enriched = dict(result)
    enriched["ok"] = True

    battle = build_battle_block(result, user)
    if battle:
        enriched["battle"] = battle

    if enriched.get("player_level_up") is not None and "level_up" not in enriched:
        enriched["level_up"] = bool(enriched.get("player_level_up"))

    return enriched


def wrap_boss_start_state(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("error"):
        return {**state, "ok": False}
    return {**state, "ok": True, "active": True}
