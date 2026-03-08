# handlers/effects_manager.py
"""
СИСТЕМА ЭФФЕКТОВ v2.0 (исправленная + SQLite)
Версия: 2.0.5 (Fix None inventory)
"""

from items import SHOP_ITEMS

ITEM_TYPES = {
    "permanent",
    "consumable_single_use",
    "consumable_on_demand",
    "island_bound_temporary",
    "one_time_risk",
    "level_wide_risk"
}

EFFECT_DEFINITIONS = {
    "ignore_mistake_penalty": {
        "type": "permanent",
        "applies_to": "task_mistake",
        "modifier_key": "mistake_penalty_ignored",
        "default_value": False,
    },
    "hint_is_free": {
        "type": "permanent",
        "applies_to": "hint_usage",
        "modifier_key": "hint_is_free",
        "default_value": False,
    },
    "add_x_xp_per_task": {
        "type": "permanent",
        "applies_to": "xp_gain",
        "modifier_key": "xp_bonus_per_task",
        "default_value": 0,
        "param": "value",
    },
    "multiply_points_by_x": {
        "type": "permanent",
        "applies_to": "score_gain",
        "modifier_key": "point_multiplier",
        "default_value": 1.0,
        "param": "multiplier",
    },
    "add_x_points_per_boss_win": {
        "type": "permanent",
        "applies_to": "boss_win_reward",
        "modifier_key": "boss_win_bonus_points",
        "default_value": 0,
        "param": "value",
    },
    "additive_progressive": {
        "type": "island_bound_temporary",
        "applies_to": "score_gain",
        "modifier_key": "progressive_score_bonus",
        "default_value": 0,
        "param": "value",
    },
    "double_on_equal_operands": {
        "type": "island_bound_temporary",
        "applies_to": "score_gain",
        "modifier_key": "double_equal_operands",
        "default_value": False,
    },
    "partial_penalty_refund": {
        "type": "island_bound_temporary",
        "applies_to": "task_mistake",
        "modifier_key": "penalty_refund_ratio",
        "default_value": 0.0,
        "param": "refund_ratio",
    },
    "ignore_first_mistake": {
        "type": "island_bound_temporary",
        "applies_to": "task_mistake",
        "modifier_key": "ignore_first_mistake",
        "default_value": False,
    },
    "perfect_run_bonus": {
        "type": "island_bound_temporary",
        "applies_to": "boss_win_reward",
        "modifier_key": "perfect_run_bonus",
        "default_value": 0,
        "param": "bonus",
    },
    "risk_reward": {
        "type": "one_time_risk",
        "applies_to": "score_gain",
        "modifier_key": "risk_reward_active",
        "default_value": False,
        "success_bonus": "success_bonus",
        "failure_penalty": "failure_penalty",
    },
    "chaos": {
        "type": "one_time_risk",
        "applies_to": "score_gain",
        "modifier_key": "chaos_active",
        "default_value": False,
        "success_reward": "success_reward",
        "failure_penalty": "failure_penalty",
    },
    "dice_roll": {
        "type": "one_time_risk",
        "applies_to": "pre_task",
        "modifier_key": "dice_roll_active",
        "default_value": False,
    },
    "inverted_scoring": {
        "type": "level_wide_risk",
        "applies_to": "score_gain",
        "modifier_key": "inverted_scoring_active",
        "default_value": False,
        "error_reward": "error_reward",
        "correct_reward": "correct_reward",
        "cancel_cost": "cancel_cost",
    },
}


def _process_item_effect(item_id, item_data, modifiers):
    effect_name = item_data.get("effect")
    item_type = item_data.get("type")

    if not effect_name or not item_type or item_type not in ITEM_TYPES:
        return

    if item_id == "math_crown":
        modifiers['hint_is_free'] = True
        modifiers['mistake_penalty_ignored'] = True
        crown_point_mult = item_data.get("multiplier", 1.0)
        modifiers['point_multiplier'] = modifiers.get('point_multiplier', 1.0) * crown_point_mult
        crown_xp_mult = item_data.get("xp_multiplier", 1.0)
        modifiers['xp_multiplier'] = modifiers.get('xp_multiplier', 1.0) * crown_xp_mult
        crown_xp_bonus = item_data.get("xp_bonus_per_task", 0)
        modifiers['xp_bonus_per_task'] = modifiers.get('xp_bonus_per_task', 0) + crown_xp_bonus
        crown_boss_bonus = item_data.get("boss_win_bonus_points", 0)
        modifiers['boss_win_bonus_points'] = modifiers.get('boss_win_bonus_points', 0) + crown_boss_bonus
        modifiers['has_unlocked_secret'] = True
        return

    definition = EFFECT_DEFINITIONS.get(effect_name)
    if not definition or definition["type"] != item_type:
        return

    mod_key = definition["modifier_key"]
    default_val = definition["default_value"]

    if mod_key not in modifiers:
        modifiers[mod_key] = default_val

    if "param" in definition:
        param_name = definition["param"]
        param_value = item_data.get(param_name)
        if param_value is not None:
            if isinstance(modifiers[mod_key], (int, float)):
                modifiers[mod_key] += param_value
            elif isinstance(modifiers[mod_key], bool):
                modifiers[mod_key] = True

    if item_type in ["one_time_risk", "level_wide_risk"]:
        modifiers[mod_key] = True
        for key in ["success_bonus", "failure_penalty", "success_reward", "error_reward", "correct_reward", "cancel_cost"]:
            if key in item_data:
                modifiers[f"{effect_name}_{key}"] = item_data[key]


def calculate_modifiers(user_id, storage=None):
    """Вычисляет все активные модификаторы для пользователя."""
    if storage:
        progress = storage.get_user(user_id) or {}
    else:
        progress = {}
    
    # ✅ ИСПРАВЛЕНО: inventory может быть None
    inventory = progress.get("inventory", []) or []

    modifiers = {
        'point_multiplier': 1.0,
        'xp_bonus_per_task': 0,
        'xp_multiplier': 1.0,
        'hint_is_free': False,
        'mistake_penalty_ignored': False,
        'boss_win_bonus_points': 0,
        'progressive_score_bonus': 0,
        'double_equal_operands': False,
        'penalty_refund_ratio': 0.0,
        'ignore_first_mistake': False,
        'perfect_run_bonus': 0,
        'risk_reward_active': False,
        'chaos_active': False,
        'dice_roll_active': False,
        'inverted_scoring_active': False,
        'has_unlocked_secret': False,
        'errors_this_level': 0,
    }

    inventory_items_count = {}
    for item_id in inventory:
        inventory_items_count[item_id] = inventory_items_count.get(item_id, 0) + 1

    for item_id, count in inventory_items_count.items():
        item_data = SHOP_ITEMS.get(item_id)
        if not item_data:
            continue
        _process_item_effect(item_id, item_data, modifiers)

    return modifiers


def apply_consumable_effect(user_id, item_id_to_apply, storage=None):
    """Применяет одноразовый эффект и удаляет ВСЕ копии предмета."""
    if not storage:
        return False, {}
    
    progress = storage.get_user(user_id) or {}
    inventory = progress.get("inventory", []) or []  # ✅ ИСПРАВЛЕНО
    
    if item_id_to_apply not in inventory:
        return False, {}

    item_data = SHOP_ITEMS.get(item_id_to_apply)
    if not item_data:
        return False, {}

    inventory = [item for item in inventory if item != item_id_to_apply]
    progress["inventory"] = inventory
    storage.save_user(user_id, progress)

    return True, item_data


def get_alchemy_item_by_id(item_id):
    return SHOP_ITEMS.get(item_id)