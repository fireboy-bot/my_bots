"""
Единые HTTP-обёртки для Flask API (additive: поле ok, без ломания старых полей).
"""

from typing import Any, Dict, Tuple

from flask import jsonify

from core.boss_common import enrich_game_response, wrap_boss_start_state


NOT_FOUND_MESSAGE = "Игрок не найден"


def engine_error_status(result: Dict[str, Any], not_found_message: str = NOT_FOUND_MESSAGE) -> int:
    if result.get("error") == not_found_message:
        return 404
    return 403


def engine_json(result: Dict[str, Any], status: int = 200):
    return jsonify(result), status


def engine_result(
    result: Dict[str, Any],
    *,
    not_found_message: str = NOT_FOUND_MESSAGE,
    enrich_user: Any = None,
) -> Tuple[Any, int]:
    if result.get("error"):
        payload = enrich_game_response(result, enrich_user)
        return engine_json(payload, engine_error_status(result, not_found_message))

    payload = enrich_game_response(result, enrich_user)
    return engine_json(payload)


def boss_start_result(result: Dict[str, Any]) -> Tuple[Any, int]:
    if result.get("error"):
        return engine_result(result)
    return engine_json(wrap_boss_start_state(result))


def boss_state_result(result: Dict[str, Any]) -> Tuple[Any, int]:
    if result.get("error"):
        return engine_json({**result, "ok": False}, 404 if result["error"] == NOT_FOUND_MESSAGE else 400)
    if not result.get("active"):
        return engine_json({**result, "ok": True})
    return engine_json({**result, "ok": True, "active": True})
