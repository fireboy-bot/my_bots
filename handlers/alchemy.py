# handlers/alchemy.py
"""
Лавка Безумца — алхимические рецепты и рисковые артефакты.
Версия: 2.1 (Fix balance sync bug) 🗄️⚗️💰🐛

Исправление:
- После spend_score() обновляем локальный progress["score_balance"]
- Чтобы финальный save_user() не перезаписал новый баланс старым значением
"""

import json
import os
import logging
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BASE_DIR
from items import SHOP_ITEMS
from handlers.utils import load_json

logger = logging.getLogger(__name__)


def get_all_items():
    """Возвращает все предметы"""
    return SHOP_ITEMS


# Рецепты алхимии
ALCHEMY_RECIPES = {
    "bravery_potion": {"cost_in_score": 150, "unlocks_after": "subtraction"},
    "chaos_cup": {"cost_in_score": 250, "unlocks_after": "multiplication"},
    "dice_of_fate": {"cost_in_score": 180, "unlocks_after": "division"},
    "madness_potion": {"cost_in_score": 200, "unlocks_after": "completed_normal_game"}
}


def get_available_recipes(progress):
    """
    Возвращает список рецептов, доступных для создания.
    """
    available = []
    unlocked_zones = set(progress.get("unlocked_zones", []))
    completed_normal_game = progress.get("completed_normal_game", False)
    
    for item_id, recipe in ALCHEMY_RECIPES.items():
        unlock_condition = recipe.get("unlocks_after", None)
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


def get_alchemy_inline_keyboard(available_items, current_balance):
    """Генерирует inline-кнопки ПОД сообщением"""
    keyboard = []
    
    for item_id in available_items:
        all_items = get_all_items()
        item = all_items[item_id]
        recipe = ALCHEMY_RECIPES[item_id]
        cost_in_score = item.get("cost_in_score", recipe["cost_in_score"])
        can_afford = current_balance >= cost_in_score
        
        if can_afford:
            button_text = f"⚗️ Создать {item['name']} ({cost_in_score})"
            callback_data = f"craft_{item_id}"
        else:
            button_text = f"❌ {item['name']} ({cost_in_score}) — недоступно"
            callback_data = "noop"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Кнопка возврата
    keyboard.append([InlineKeyboardButton("⬅️ Назад в игру", callback_data="back_to_game")])
    
    return InlineKeyboardMarkup(keyboard)


async def show_alchemy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    progress = storage.get_user(user_id) or {}
    
    available_recipes = get_available_recipes(progress)
    
    # ✅ ИСПРАВЛЕНО: используем score_balance как валюту
    current_balance = progress.get("score_balance", 0)
    total_rating = progress.get("total_score", 0)
    
    msg = "💀 **ЛАВКА БЕЗУМЦА**\n\n"
    msg += f"💰 Твой баланс: *{current_balance} очков*\n"
    msg += f"🏆 Твой рейтинг: *{total_rating} очков*\n\n"
    msg += "ХА-ХА-ХА! Добро пожаловать в мою лабораторию хаоса!\n"
    msg += "Преврати свои очки в безумные артефакты... если осмелишься!\n\n"
    
    all_items = get_all_items()
    for item_id in available_recipes:
        if item_id not in ALCHEMY_RECIPES:
            continue
        recipe = ALCHEMY_RECIPES[item_id]
        item = all_items[item_id]
        item_name = item["name"]
        description = item.get("description", "Особый артефакт.")
        cost_in_score = item.get("cost_in_score", recipe["cost_in_score"])
        can_afford = current_balance >= cost_in_score
        
        status = "✅" if can_afford else "❌"
        msg += f"{status} **{item_name}**\n"
        msg += f"   💰 Цена: {cost_in_score} очков\n"
        msg += f"   ℹ️ {description}\n\n"
    
    if not available_recipes:
        msg += "🔒 Нет доступных рецептов.\n"
        msg += "Продолжай исследовать Числяндию, чтобы открыть новые артефакты!\n"
        if not progress.get("completed_normal_game", False):
            msg += "- Победи Финального Владыку\n"
    
    msg += "\n📌 **Как создать?**\n"
    msg += "Нажми на кнопку под сообщением!"
    
    reply_markup = get_alchemy_inline_keyboard(available_recipes, current_balance)
    
    # ✅ ИСПРАВЛЕНО: путь через BASE_DIR
    image_path = os.path.join(BASE_DIR, 'images', 'alchemist_mad.jpg')
    
    try:
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=msg,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        logger.warning(f"🖼️ Аватарка не найдена: {image_path}")
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"❌ Ошибка отправки алхимии: {e}")
        await update.message.reply_text("⚠️ Ошибка загрузки лавки. Попробуй позже.")


async def execute_craft(user_id: int, item_id: str, storage, score_manager=None) -> tuple[bool, str]:
    """
    Выполняет создание артефакта.
    
    Args:
        user_id: ID пользователя
        item_id: ID предмета
        storage: Экземпляр PlayerStorage
        score_manager: Экземпляр ScoreManager (опционально)
    
    Returns:
        (success: bool, message: str)
    """
    progress = storage.get_user(user_id) or {}
    inventory = progress.get("inventory", [])
    
    # ✅ ИСПРАВЛЕНО: используем score_balance как валюту
    current_balance = progress.get("score_balance", 0)
    
    if item_id not in ALCHEMY_RECIPES:
        logger.error(f"❌ Рецепт не найден: {item_id}")
        return False, "❌ Рецепт не найден!"
    
    all_items = get_all_items()
    
    if item_id not in all_items:
        logger.error(f"❌ Предмет не найден в SHOP_ITEMS: {item_id}")
        return False, "❌ Предмет не найден!"
    
    item_data = all_items[item_id]
    cost_in_score = item_data.get("cost_in_score")
    item_type = item_data.get("type", "one_time_risk")
    
    # Проверки
    if current_balance < cost_in_score:
        return False, f"❌ Недостаточно очков (нужно {cost_in_score}, есть {current_balance})!"
    
    # Для one-time предметов: проверяем, не создан ли уже
    if item_type in ["one_time_risk", "level_wide_risk"] and item_id in inventory:
        return False, "❌ Артефакт уже создан!"
    
    # Проверка доступности по зонам
    if item_id not in get_available_recipes(progress):
        return False, "❌ Рецепт ещё не открыт!"
    
    # ✅ СПИСАНИЕ ОЧКОВ ЧЕРЕЗ SCORE_MANAGER
    if score_manager:
        success, message = await score_manager.spend_score(
            user_id=user_id,
            amount=cost_in_score,
            reason="alchemy_craft",
            context=item_id
        )
        if not success:
            return False, message
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: обновляем локальный progress после spend_score
        # Чтобы финальный save_user() не перезаписал новый баланс старым значением
        progress["score_balance"] = max(0, progress.get("score_balance", 0) - cost_in_score)
    else:
        # Fallback: прямое списание (если score_manager не инициализирован)
        if current_balance < cost_in_score:
            return False, "❌ Недостаточно очков!"
        progress["score_balance"] = current_balance - cost_in_score
    
    # Добавляем предмет в инвентарь (только если не был создан)
    if item_id not in inventory:
        inventory.append(item_id)
        progress["inventory"] = inventory
    
    # ✅ СОХРАНЯЕМ ЧЕРЕЗ PlayerStorage
    storage.save_user(user_id, progress)
    
    logger.info(f"⚗️ Пользователь {user_id} создал {item_id} за {cost_in_score} очков")
    
    return True, f"✨ Создано: {item_data['name']}!"


def get_alchemy_activation_message(item_id: str) -> str:
    """Возвращает сообщение об активации эффекта алхимического артефакта."""
    if item_id not in get_all_items():
        return ""
    
    all_items = get_all_items()
    item_data = all_items[item_id]
    item_name = item_data["name"]
    item_effect = item_data.get("effect")
    item_type = item_data.get("type")
    
    message = f"✨ Ты создала **{item_name}**!\n\n"
    
    if item_type == "one_time_risk":
        message += "⚠️ *Эффект сработает на следующей задаче!*\n\n"
        if item_effect == "risk_reward":
            success_bonus = item_data.get("success_bonus", 0)
            failure_penalty = item_data.get("failure_penalty", 0)
            message += f"💣 *Эффект активирован!* Следующая задача: +{success_bonus} за успех, {failure_penalty} за ошибку!"
        elif item_effect == "chaos":
            success_reward = item_data.get("success_reward", 0)
            failure_penalty = item_data.get("failure_penalty", 0)
            message += f"💣 *Эффект активирован!* Следующая задача: +{success_reward} за успех, {failure_penalty} за ошибку!"
        elif item_effect == "dice_roll":
            message += "🎲 *Эффект активирован!* Перед следующей задачей будет брошен кубик судьбы!"
    elif item_type == "level_wide_risk":
        message += "🌀 *Эффект действует до конца уровня!*\n\n"
        if item_effect == "inverted_scoring":
            error_reward = item_data.get("error_reward", 0)
            correct_reward = item_data.get("correct_reward", 0)
            cancel_cost = item_data.get("cancel_cost", 0)
            message += f"🌀 *Эффект активирован!* На этом уровне: ошибки = +{error_reward}, правильные = {correct_reward}."
            message += f"\nОтменить можно за {cancel_cost} очков."
    
    message += "\n\n💡 Артефакт добавлен в инвентарь!"
    
    return message


async def handle_alchemy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback'ов алхимии."""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    storage = context.bot_data.get('storage')
    score_manager = context.bot_data.get('score_manager')
    
    if not storage:
        await query.edit_message_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    # Обрабатываем ТОЛЬКО команды алхимии
    if not (data == "back_to_game" or data.startswith("craft_")):
        return
    
    if data == "back_to_game":
        if query.message.photo:
            await query.edit_message_caption("Возвращаюсь в игру...")
        else:
            await query.edit_message_text("Возвращаюсь в игру...")
        return
    
    if data.startswith("craft_"):
        item_id = data[6:]  # craft_ = 6 символов
        all_items = get_all_items()
        
        if item_id not in all_items:
            error_msg = "❌ Артефакт не найден!"
            if query.message.photo:
                await query.edit_message_caption(error_msg)
            else:
                await query.edit_message_text(error_msg)
            return
        
        success, message = await execute_craft(user_id, item_id, storage, score_manager)
        
        if success:
            activation_message = get_alchemy_activation_message(item_id)
        else:
            activation_message = message
        
        # Универсальное редактирование
        try:
            if query.message.photo:
                await query.edit_message_caption(activation_message, parse_mode="Markdown")
            else:
                await query.edit_message_text(activation_message, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отредактировать сообщение: {e}")
            # Если редактирование не удалось, отправляем новое сообщение
            await update.effective_message.reply_text(activation_message, parse_mode="Markdown")