"""
Алхимия (Лавка Безумца) — ядро без зависимости от Telegram.
"""

import logging
from typing import List, Tuple

from items import SHOP_ITEMS

logger = logging.getLogger(__name__)

ALCHEMY_RECIPES = {
    "bravery_potion": {"cost_in_score": 150, "unlocks_after": "subtraction"},
    "chaos_cup": {"cost_in_score": 250, "unlocks_after": "multiplication"},
    "dice_of_fate": {"cost_in_score": 180, "unlocks_after": "division"},
    "madness_potion": {"cost_in_score": 200, "unlocks_after": "completed_normal_game"},
}


def get_all_items():
    return SHOP_ITEMS


def get_available_recipes(progress) -> List[str]:
    available = []
    unlocked_zones = set(progress.get("unlocked_zones", []))
    completed_normal_game = progress.get("completed_normal_game", False)

    for item_id, recipe in ALCHEMY_RECIPES.items():
        unlock_condition = recipe.get("unlocks_after")
        is_unlocked = False

        if unlock_condition is None:
            is_unlocked = True
        elif unlock_condition == "subtraction":
            is_unlocked = "subtraction" in unlocked_zones
        elif unlock_condition == "multiplication":
            is_unlocked = "multiplication" in unlocked_zones
        elif unlock_condition == "division":
            is_unlocked = "division" in unlocked_zones
        elif unlock_condition == "completed_normal_game":
            is_unlocked = completed_normal_game

        if is_unlocked:
            available.append(item_id)

    return available


def craft_alchemy_item(user_id, item_id: str, storage, score_manager=None) -> Tuple[bool, str]:
    uid = storage._extract_numeric_user_id(user_id)
    progress = storage.get_user(uid) or {}
    inventory = list(progress.get("inventory") or [])
    current_balance = progress.get("score_balance", 0)

    if item_id not in ALCHEMY_RECIPES:
        return False, "❌ Рецепт не найден!"

    all_items = get_all_items()
    if item_id not in all_items:
        return False, "❌ Предмет не найден!"

    item_data = all_items[item_id]
    cost_in_score = item_data.get("cost_in_score", ALCHEMY_RECIPES[item_id]["cost_in_score"])
    item_type = item_data.get("type", "one_time_risk")

    if current_balance < cost_in_score:
        return False, f"❌ Недостаточно золотых (нужно {cost_in_score}, есть {current_balance})!"

    if item_type in ["one_time_risk", "level_wide_risk"] and item_id in inventory:
        return False, "❌ Артефакт уже создан!"

    if item_id not in get_available_recipes(progress):
        return False, "❌ Рецепт ещё не открыт!"

    if score_manager:
        success, message = score_manager.spend_score(
            user_id=str(uid),
            amount=cost_in_score,
            reason="alchemy_craft",
            context=item_id,
        )
        if not success:
            return False, message
    else:
        progress["score_balance"] = current_balance - cost_in_score
        storage.save_user(uid, progress)

    progress = storage.get_user(uid) or progress
    inventory = list(progress.get("inventory") or [])
    if item_id not in inventory:
        inventory.append(item_id)
    progress["inventory"] = inventory

    if not storage.save_user(uid, progress):
        logger.error(f"save_user failed after alchemy craft user={uid} item={item_id}")
        return False, "❌ Ошибка сохранения покупки"

    logger.info(f"User {uid} crafted {item_id} for {cost_in_score} gold")
    return True, f"✨ Создано: {item_data['name']}!"


def get_alchemy_activation_message(item_id: str) -> str:
    all_items = get_all_items()
    if item_id not in all_items:
        return ""

    item_data = all_items[item_id]
    item_name = item_data["name"]
    item_effect = item_data.get("effect")
    item_type = item_data.get("type")

    message = f"✨ Ты создала {item_name}!\n\n"

    if item_type == "one_time_risk":
        message += "⚠️ Эффект сработает на следующей задаче!\n\n"
        if item_effect == "risk_reward":
            message += (
                f"💣 Следующая задача: +{item_data.get('success_bonus', 0)} за успех, "
                f"{item_data.get('failure_penalty', 0)} за ошибку!"
            )
        elif item_effect == "chaos":
            message += (
                f"💣 Следующая задача: +{item_data.get('success_reward', 0)} за успех, "
                f"{item_data.get('failure_penalty', 0)} за ошибку!"
            )
        elif item_effect == "dice_roll":
            message += "🎲 Перед следующей задачей будет брошен кубик судьбы!"
    elif item_type == "level_wide_risk":
        message += "🌀 Эффект действует до конца уровня!\n\n"
        if item_effect == "inverted_scoring":
            message += (
                f"🌀 Ошибки = +{item_data.get('error_reward', 0)}, "
                f"правильные = {item_data.get('correct_reward', 0)}."
            )

    message += "\n\n💡 Артефакт добавлен в инвентарь!"
    return message
