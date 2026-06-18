"""
Эпический бой с Истинным Владыкой — web-версия (по мотивам handlers/true_lord_battle.py).
"""

import json
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from config import BOSS_DATA_DIR
from core.boss_common import (
    get_modifiers,
    invalid_numeric_response,
    normalize_boss_task,
    parse_numeric_answer,
    refresh_user_scores,
)
from core.boss_run import TRUE_LORD_ID, can_start_boss, unlock_new_zones
from core.level_run import _apply_xp_level_up

TRUE_LORD_MAX_HP = 20
TRUE_LORD_TASK_COUNT = 60
TRUE_LORD_REWARD = "душа_числяндии"

PHASE_THRESHOLDS = {
    "calm": 70,
    "angry": 30,
    "desperate": 0,
}

PHASE_NAMES = {
    "calm": "Надменный",
    "angry": "Встревоженный",
    "desperate": "В панике",
}

PHASE_MESSAGES = {
    "angry": "Это… не соответствует расчётам. Подожди… так не должно быть.",
    "desperate": "НЕТ! Порядок не может ошибаться! Это невозможно… невозможно…",
}

LAST_MESSAGES = {
    "calm": [
        "Ошибка невозможна. Всё уже решено.",
        "Ваши попытки… не влияют на результат.",
        "В Числяндии существует только один правильный ответ.",
        "Я — порядок. А порядок не проигрывает.",
        "Вы ещё не поняли правила. А я их создал.",
    ],
    "angry": [
        "Это… не соответствует расчётам.",
        "Подожди… так не должно быть.",
        "Повтори вычисление. Результат неверен.",
        "Порядок колеблется… но он устоит.",
        "Нет. Это просто погрешность.",
    ],
    "desperate": [
        "Стой! Это нарушает систему!",
        "Такого ответа не существует!",
        "Я… я всё просчитал!",
        "НЕТ! Порядок не может ошибаться!",
        "Остановитесь! Я ещё могу всё исправить!",
    ],
}

GEORGY_JOKES = {
    "addition": [
        "Так… числа сложились, но как моя слизь в рюкзаке — не совсем аккуратно.",
        "Ой, тут плюсик вроде был, а стал минусом. У меня так же, когда путаю завтрак и ужин.",
        "Сложили мы всё правильно… почти. Как носки после стирки — один лишний.",
    ],
    "subtraction": [
        "Мы тут вычли так, что я аж похудел. А я этого не просил!",
        "Минус — штука коварная. У меня от него слизь иногда убегает.",
        "Кажется, мы вычли больше, чем нужно. Это как откусить сразу половину бутерброда.",
    ],
    "multiplication": [
        "Ого! Тут чисел стало больше, чем моих следов после дождя.",
        "Умножение — это когда всё растёт. А тут что-то выросло криво… как я без зарядки.",
        "Мне нравится этот ответ. Но правильному он не родственник.",
    ],
    "division": [
        "Поделили так, что всем не хватило. Я такое видел на дне рождения без торта.",
        "Деление любит аккуратность. А тут получилось… по-слизневски.",
        "Так делить нельзя. Проверено моей слизью — она потом обижается.",
    ],
    "general": [
        "Стоп-стоп! Мы так быстро пошли, что я отстал на два сантиметра.",
        "Когда спешишь, числа начинают шалить. Проверено мной и моей слизью.",
        "Давай медленно. Я вообще-то чемпион мира по медленности.",
        "Читаем ещё раз. Я вот иногда читаю, а думаю о капусте.",
        "Задание хитрое. Почти как моя слизь, когда прячется.",
        "Кажется, мы решили не ту задачу. Но это тоже опыт!",
        "О! Старая знакомая ошибка. Я с ней уже чай пил.",
        "Ничего страшного. Я вот однажды три раза подряд сел не на тот лист.",
        "Ошибки иногда возвращаются. Как я после прогулки.",
    ],
}

SUCCESS_MESSAGES = {
    "calm": "Ты... угодала? Везение.",
    "angry": "Это... невозможно!",
    "desperate": "Ты... не должна быть... такой сильной...!",
}

MANUNYA_SUPPORT = {
    "angry": "Он злится! Это значит, ты на правильном пути!",
    "desperate": "Морковка, не слушай его! Это всё обман!",
}

SECRET_TEXT = (
    "Ты заметила то, что не все видят…\n"
    "Ошибка — это не поражение.\n"
    "Это путь к пониманию.\n\n"
    "«Если бы я понял это раньше,\n"
    "Числяндия не нуждалась бы в спасении.»"
)

FINALE_TEXT = (
    "Порядок рушится… и Числяндия просыпается.\n\n"
    "Истинный Владыка исчезает, а цифры больше не боятся ошибок.\n\n"
    "Ты победила не силой — а умением рассуждать.\n"
    "Не потому что всё знала, а потому что не сдавалась."
)

_BOSS_DATA: Optional[Dict[str, Any]] = None


def _load_boss_data() -> Dict[str, Any]:
    global _BOSS_DATA
    if _BOSS_DATA is None:
        path = os.path.join(BOSS_DATA_DIR, "true_lord.json")
        with open(path, "r", encoding="utf-8") as f:
            _BOSS_DATA = json.load(f)
    return _BOSS_DATA


def get_phase(hp: int, max_hp: int = TRUE_LORD_MAX_HP) -> str:
    percent = (hp / max_hp) * 100 if max_hp else 0
    if percent <= PHASE_THRESHOLDS["desperate"]:
        return "desperate"
    if percent <= PHASE_THRESHOLDS["angry"]:
        return "angry"
    return "calm"


def avatar_url(phase: str) -> str:
    return f"/images/true_lord_{phase}.jpg"


def _classify_error_type(question: str) -> str:
    q = question.lower()
    if "слож" in q or "+" in q:
        return "addition"
    if "вычит" in q or "-" in q:
        return "subtraction"
    if "умнож" in q or "*" in q or "×" in q:
        return "multiplication"
    if "делен" in q or "/" in q or "÷" in q:
        return "division"
    return "general"


def _dialogue(speaker: str, text: str, **extra) -> Dict[str, Any]:
    return {"speaker": speaker, "text": text, **extra}


def _select_tasks() -> List[Dict[str, Any]]:
    data = _load_boss_data()
    tasks = list(data.get("tasks") or [])
    if not tasks:
        return []
    pool = tasks
    if len(pool) < TRUE_LORD_TASK_COUNT:
        multiplier = (TRUE_LORD_TASK_COUNT // len(pool)) + 1
        pool = (tasks * multiplier)[:TRUE_LORD_TASK_COUNT]
    return random.sample(pool, min(TRUE_LORD_TASK_COUNT, len(pool)))


def _normalize_task(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
    return normalize_boss_task(raw, TRUE_LORD_ID, idx)


def _build_intro_dialogues() -> List[Dict[str, Any]]:
    data = _load_boss_data()
    intro = data.get("intro", "").replace("*", "")
    return [
        _dialogue("true_lord", "👑👑 ИСТИННЫЙ ВЛАДЫКА ЧИСЛЯНДИИ", style="title"),
        _dialogue("true_lord", intro),
        _dialogue("manunya", "Будь осторожна, Морковка!"),
        _dialogue("georgy", "Это он! Главный злодей!"),
    ]


def _build_psychological_dialogues(
    progress: Dict[str, Any],
    was_correct: bool,
    phase_before: str,
    consecutive_before: int,
) -> Tuple[List[Dict[str, Any]], str]:
    dialogues: List[Dict[str, Any]] = []
    hp = int(progress.get("boss_health", TRUE_LORD_MAX_HP))
    phase_after = get_phase(hp)

    if phase_after != phase_before:
        phase_msg = PHASE_MESSAGES.get(phase_after, f"Фаза {PHASE_NAMES.get(phase_after, phase_after)}")
        dialogues.append(_dialogue("true_lord", phase_msg, phase_change=True))
        support = MANUNYA_SUPPORT.get(phase_after)
        if support:
            dialogues.append(_dialogue("manunya", support))

    if not was_correct:
        pool = LAST_MESSAGES.get(phase_after, LAST_MESSAGES["calm"])
        dialogues.append(_dialogue("true_lord", random.choice(pool)))
        tasks = progress.get("selected_boss_tasks") or []
        idx = int(progress.get("boss_task_index", 0))
        question = tasks[idx].get("question", "") if idx < len(tasks) else ""
        error_type = _classify_error_type(question)
        dialogues.append(_dialogue("manunya", "Всё в порядке! Просто подумай ещё!"))
        dialogues.append(_dialogue("georgy", random.choice(GEORGY_JOKES.get(error_type, GEORGY_JOKES["general"]))))
    else:
        consecutive = int(progress.get("true_lord_consecutive_successes", 0))
        if consecutive_before < 5 <= consecutive:
            dialogues.append(_dialogue("true_lord", SUCCESS_MESSAGES.get(phase_after, "...")))
            encouragements = [
                "Вот это да! Ты просто огонь!",
                "Он уже злится! Продолжай в том же духе!",
                "Ты почти победила! Не сбавляй обороты!",
            ]
            dialogues.append(_dialogue("manunya", random.choice(encouragements)))
            georgy_success = [
                "Вот! Теперь красиво. Прямо как моя слизь после дождя.",
                "Я горжусь. И слизь тоже.",
                "Запомни этот момент. Он вкусный. Почти как салат.",
                "Между прочим… ты думаешь лучше, чем я. А это уже серьёзно.",
            ]
            dialogues.append(_dialogue("georgy", random.choice(georgy_success)))
        else:
            dialogues.append(_dialogue("manunya", "Держись, Морковка! Ты крутая!"))
            dialogues.append(_dialogue("georgy", "Так держать! Он всё ревёт!"))

    return dialogues, phase_after


def get_true_lord_state(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not user.get("in_boss_battle") or user.get("current_boss") != TRUE_LORD_ID:
        return None
    if not user.get("true_lord_epic"):
        return None

    tasks = user.get("selected_boss_tasks") or []
    idx = int(user.get("boss_task_index", 0))
    hp = int(user.get("boss_health", TRUE_LORD_MAX_HP))
    phase = get_phase(hp)
    task = _normalize_task(tasks[idx], idx) if idx < len(tasks) else None

    return {
        "boss_id": TRUE_LORD_ID,
        "boss_name": _load_boss_data().get("name", "Истинный Владыка"),
        "boss_emoji": "👁️",
        "boss_health": hp,
        "boss_max_health": TRUE_LORD_MAX_HP,
        "task_index": idx + 1 if task else idx,
        "total_tasks": len(tasks),
        "task": task,
        "phase": phase,
        "phase_name": PHASE_NAMES.get(phase, phase),
        "avatar_url": avatar_url(phase),
        "consecutive_successes": int(user.get("true_lord_consecutive_successes", 0)),
        "error_count": int(user.get("true_lord_error_count", 0)),
        "used_hint": bool(user.get("true_lord_used_hint")),
        "epic": True,
    }


def start_true_lord_run(storage, user_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user:
        return {"error": "Игрок не найден"}

    allowed, lock_reason = can_start_boss(user, TRUE_LORD_ID)
    if not allowed:
        return {"error": f"🔒 {lock_reason}"}

    if user.get("in_boss_battle") and user.get("current_boss") == TRUE_LORD_ID and user.get("true_lord_epic"):
        state = get_true_lord_state(user)
        if state and state.get("task"):
            return {**state, "resumed": True, "dialogues": []}

    selected = _select_tasks()
    if not selected:
        return {"error": "Задачи Истинного Владыки не найдены"}

    user.update(
        {
            "in_boss_battle": True,
            "current_boss": TRUE_LORD_ID,
            "true_lord_epic": True,
            "selected_boss_tasks": selected,
            "boss_task_index": 0,
            "boss_health": TRUE_LORD_MAX_HP,
            "boss_max_health": TRUE_LORD_MAX_HP,
            "boss_turn": 0,
            "boss_abilities_used": [],
            "true_lord_error_count": 0,
            "true_lord_consecutive_successes": 0,
            "true_lord_used_hint": user.get("true_lord_used_hint", False),
            "true_lord_secret_unlocked": user.get("true_lord_secret_unlocked", False),
            "current_level": None,
            "selected_tasks": [],
            "current_task_index": 0,
        }
    )
    storage.save_user(user_id, user)

    state = get_true_lord_state(user) or {}
    data = _load_boss_data()
    return {
        **state,
        "resumed": False,
        "intro": data.get("intro", ""),
        "dialogues": _build_intro_dialogues(),
    }


def exit_true_lord_run(storage, user_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user or not user.get("in_boss_battle") or user.get("current_boss") != TRUE_LORD_ID:
        return {"success": True, "message": "Бой не активен"}

    user.update(
        {
            "in_boss_battle": False,
            "current_boss": None,
            "true_lord_epic": False,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "boss_health": TRUE_LORD_MAX_HP,
            "boss_abilities_used": [],
        }
    )
    storage.save_user(user_id, user)
    return {"success": True, "message": "↩️ Вышла из боя"}


def process_true_lord_hint(storage, score_manager, user_id: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user or not user.get("in_boss_battle") or user.get("current_boss") != TRUE_LORD_ID:
        return {"error": "Нет активного боя с Истинным Владыкой"}

    tasks = user.get("selected_boss_tasks") or []
    idx = int(user.get("boss_task_index", 0))
    if idx >= len(tasks):
        return {"error": "Нет активной задачи"}

    modifiers = get_modifiers(user_id, storage)
    penalty = 0 if modifiers.get("hint_is_free") else 10
    xp_penalty = 0 if modifiers.get("hint_is_free") else 5

    if penalty > 0:
        if score_manager:
            score_manager.spend_score(user_id, penalty, "true_lord_hint", "hint")
        else:
            user["score_balance"] = max(0, user.get("score_balance", 0) - penalty)
    if xp_penalty > 0:
        user["xp"] = max(0, user.get("xp", 0) - xp_penalty)

    refreshed = storage.get_user(user_id) or user
    refreshed["true_lord_used_hint"] = True
    if xp_penalty > 0 and not score_manager:
        refreshed["xp"] = user["xp"]
    storage.save_user(user_id, refreshed)

    hint = tasks[idx].get("hint", "")
    return {
        "success": True,
        "hint": hint,
        "penalty": penalty,
        "message": f"💡 Подсказка{' (бесплатно!)' if penalty == 0 else f' (−{penalty} очков)'}",
        "new_balance": refreshed.get("score_balance", 0),
    }


def process_true_lord_answer(storage, score_manager, user_id: str, answer: str) -> Dict[str, Any]:
    user = storage.get_user(user_id)
    if not user or not user.get("in_boss_battle") or user.get("current_boss") != TRUE_LORD_ID:
        return {"error": "Нет активного боя с Истинным Владыкой"}

    tasks = user.get("selected_boss_tasks") or []
    idx = int(user.get("boss_task_index", 0))
    boss_health = int(user.get("boss_health", TRUE_LORD_MAX_HP))
    phase_before = get_phase(boss_health)
    consecutive_before = int(user.get("true_lord_consecutive_successes", 0))

    if idx >= len(tasks) or boss_health <= 0:
        return {"error": "Бой завершён"}

    current = tasks[idx]
    is_correct, invalid_message = parse_numeric_answer(answer, current.get("answer"))
    if invalid_message:
        return invalid_numeric_response()

    modifiers = get_modifiers(user_id, storage)
    dialogues: List[Dict[str, Any]] = []
    reward = 0
    level_up = None

    user["tasks_solved"] = user.get("tasks_solved", 0) + 1
    if is_correct:
        user["tasks_correct"] = user.get("tasks_correct", 0) + 1

    if is_correct:
        base_score = 150
        point_mult = modifiers.get("point_multiplier", 1.0) * modifiers.get("next_task_point_multiplier", 1.0)
        earned_score = int(base_score * point_mult) + modifiers.get("instant_score_gain", 0)

        if score_manager:
            score_manager.add_score(user_id, earned_score, "true_lord_correct", f"task_{idx}", apply_artifacts=False)
        else:
            user["score_balance"] = user.get("score_balance", 0) + earned_score
            user["total_score"] = user.get("total_score", 0) + earned_score
        reward = earned_score

        user = storage.get_user(user_id) or user
        base_xp = 20
        earned_xp = int((base_xp + modifiers.get("xp_bonus_per_task", 0)) * modifiers.get("xp_multiplier", 1.0))
        user, level_up = _apply_xp_level_up(user, earned_xp)

        user["boss_task_index"] = idx + 1
        user["boss_health"] = max(0, boss_health - 1)
        user["boss_turn"] = user.get("boss_turn", 0) + 1
        user["true_lord_consecutive_successes"] = consecutive_before + 1
        user["true_lord_error_count"] = 0
        message = "✅ Удар по Владыке!"

        if user["boss_health"] <= 0:
            storage.save_user(user_id, user)
            return _finalize_true_lord_victory(storage, score_manager, user_id, modifiers)

        dialogues, phase_after = _build_psychological_dialogues(user, True, phase_before, consecutive_before)
        storage.save_user(user_id, user)

        next_task = _normalize_task(tasks[idx + 1], idx + 1)
        return {
            "correct": True,
            "reward": reward,
            "message": message,
            "boss_health": user.get("boss_health", 0),
            "boss_max_health": TRUE_LORD_MAX_HP,
            "task_index": idx + 2,
            "total_tasks": len(tasks),
            "next_task": next_task,
            "phase": phase_after,
            "phase_name": PHASE_NAMES.get(phase_after, phase_after),
            "avatar_url": avatar_url(phase_after),
            "phase_changed": phase_after != phase_before,
            "dialogues": dialogues,
            "player_level_up": level_up,
            "level_up": bool(level_up),
            "new_balance": user.get("score_balance", 0),
            "new_total_score": user.get("total_score", 0),
        }

    penalty = 0 if modifiers.get("mistake_penalty_ignored") else 20
    if penalty > 0:
        if score_manager:
            score_manager.spend_score(user_id, penalty, "true_lord_wrong", f"task_{idx}")
        else:
            user["score_balance"] = max(0, user.get("score_balance", 0) - penalty)
        reward = -penalty

    user = storage.get_user(user_id) or user
    user["xp"] = max(0, user.get("xp", 0) - 10)
    user["boss_turn"] = user.get("boss_turn", 0) + 1
    user["true_lord_error_count"] = int(user.get("true_lord_error_count", 0)) + 1
    user["true_lord_consecutive_successes"] = 0

    dialogues, phase_after = _build_psychological_dialogues(user, False, phase_before, consecutive_before)
    storage.save_user(user_id, user)
    same_task = _normalize_task(current, idx)

    return {
        "correct": False,
        "reward": reward,
        "message": "❌ Промах! Владыка насмехается",
        "boss_health": user.get("boss_health", boss_health),
        "boss_max_health": TRUE_LORD_MAX_HP,
        "task_index": idx + 1,
        "total_tasks": len(tasks),
        "next_task": same_task,
        "retry_same_task": True,
        "phase": phase_after,
        "phase_name": PHASE_NAMES.get(phase_after, phase_after),
        "avatar_url": avatar_url(phase_after),
        "phase_changed": phase_after != phase_before,
        "dialogues": dialogues,
        "new_balance": user.get("score_balance", 0),
        "new_total_score": user.get("total_score", 0),
    }


def _finalize_true_lord_victory(
    storage,
    score_manager,
    user_id: str,
    modifiers: Dict[str, Any],
) -> Dict[str, Any]:
    user = storage.get_user(user_id) or {}
    data = _load_boss_data()

    victory_bonus = int(500 * modifiers.get("point_multiplier", 1.0))
    if score_manager:
        score_manager.add_score(user_id, victory_bonus, "true_lord_victory", "victory", apply_artifacts=False)

    user = storage.get_user(user_id) or {}
    if not score_manager:
        user["score_balance"] = user.get("score_balance", 0) + victory_bonus
        user["total_score"] = user.get("total_score", 0) + victory_bonus

    victory_xp = int((200 + modifiers.get("xp_bonus_per_task", 0)) * modifiers.get("xp_multiplier", 1.0))
    user, level_up = _apply_xp_level_up(user, victory_xp)

    reward_item = data.get("reward", TRUE_LORD_REWARD)
    rewards = user.get("rewards") or []
    if reward_item not in rewards:
        rewards.append(reward_item)
    user["rewards"] = rewards

    defeated = list(user.get("defeated_bosses") or [])
    if TRUE_LORD_ID not in defeated:
        defeated.append(TRUE_LORD_ID)
        user["defeated_bosses"] = defeated
        user = unlock_new_zones(user, TRUE_LORD_ID)

    user["completed_normal_game"] = True
    user["absolute_victory"] = True

    used_hint = bool(user.get("true_lord_used_hint"))
    show_secret = not used_hint and not user.get("true_lord_secret_unlocked")
    if show_secret:
        user["true_lord_secret_unlocked"] = True

    user.update(
        {
            "in_boss_battle": False,
            "current_boss": None,
            "true_lord_epic": False,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "boss_health": 0,
            "boss_max_health": 0,
            "boss_turn": 0,
            "just_completed_level": None,
            "current_level": None,
            "selected_tasks": [],
            "current_task_index": 0,
        }
    )
    storage.save_user(user_id, user)
    refreshed = storage.get_user(user_id) or user

    victory_text = data.get("victory", "").replace("*", "")
    dialogues = [
        _dialogue("true_lord", victory_text),
        _dialogue("manunya", "Морковка, ты — ЛЕГЕНДА ЧИСЛЯНДИИ!"),
        _dialogue("georgy", "Ха-ха! Я знал, что ты справишься!"),
    ]

    return {
        "correct": True,
        "boss_defeated": True,
        "boss_id": TRUE_LORD_ID,
        "absolute_victory": True,
        "reward_item": reward_item,
        "victory_bonus": victory_bonus,
        "message": f"🌟 АБСОЛЮТНАЯ ПОБЕДА! Награда: {reward_item.replace('_', ' ')}",
        "boss_health": 0,
        "dialogues": dialogues,
        "finale_text": FINALE_TEXT,
        "secret_text": SECRET_TEXT if show_secret else None,
        "player_level_up": level_up,
        "level_up": bool(level_up),
        "new_balance": refreshed.get("score_balance", 0),
        "new_total_score": refreshed.get("total_score", 0),
    }
