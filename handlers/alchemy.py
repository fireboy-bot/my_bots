# handlers/alchemy.py
"""
Лавка Безумца — алхимические рецепты и рисковые артефакты.
Версия: 3.2 (Fix: spend_score is NOT async) 🗄️⚗️🎩✅
"""

import json
import os
import logging
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BASE_DIR
from items import SHOP_ITEMS
from handlers.narrative_manager import PhraseManager, send_character_message, send_character_message_by_id

logger = logging.getLogger(__name__)
phrase_manager = PhraseManager()


def get_all_items():
    """Возвращает все предметы"""
    return SHOP_ITEMS


ALCHEMY_RECIPES = {
    "bravery_potion": {"cost_in_score": 150, "unlocks_after": "subtraction"},
    "chaos_cup": {"cost_in_score": 250, "unlocks_after": "multiplication"},
    "dice_of_fate": {"cost_in_score": 180, "unlocks_after": "division"},
    "madness_potion": {"cost_in_score": 200, "unlocks_after": "completed_normal_game"}
}


def get_available_recipes(progress):
    """Возвращает список рецептов, доступных для создания."""
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
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад в игру", callback_data="back_to_game")])
    
    return InlineKeyboardMarkup(keyboard)


async def show_alchemy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать алхимию — с аватаркой Алхимика!"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    progress = storage.get_user(user_id) or {}
    
    available_recipes = get_available_recipes(progress)
    
    current_balance = progress.get("score_balance", 0)
    total_rating = progress.get("total_score", 0)
    
    msg = "💀 **ЛАВКА БЕЗУМЦА**\n\n"
    msg += f"💰 Твой баланс: *{current_balance} золотых*\n"
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
        msg += f"   💰 Цена: {cost_in_score} золотых\n"
        msg += f"   ℹ️ {description}\n\n"
    
    if not available_recipes:
        msg += "🔒 Нет доступных рецептов.\n"
        msg += "Продолжай исследовать Числяндию, чтобы открыть новые артефакты!\n"
        if not progress.get("completed_normal_game", False):
            msg += "- Победи Финального Владыку\n"
    
    msg += "\n📌 **Как создать?**\n"
    msg += "Нажми на кнопку под сообщением!"
    
    reply_markup = get_alchemy_inline_keyboard(available_recipes, current_balance)
    
    # ✅ ОТПРАВЛЯЕМ С АВАТАРКОЙ АЛХИМИКА!
    await send_character_message(
        update, context, "alchemist",
        "🧪 *ЛАВКА БЕЗУМЦА!*\n\n«ХА-ХА-ХА! Готов рискнуть?»",
        mood="calm"
    )
    
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def execute_craft(user_id: int, item_id: str, storage, score_manager=None) -> tuple:
    """Выполняет создание артефакта."""
    progress = storage.get_user(user_id) or {}
    inventory = progress.get("inventory", [])
    
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
    
    if current_balance < cost_in_score:
        return False, f"❌ Недостаточно золотых (нужно {cost_in_score}, есть {current_balance})!"
    
    if item_type in ["one_time_risk", "level_wide_risk"] and item_id in inventory:
        return False, "❌ Артефакт уже создан!"
    
    if item_id not in get_available_recipes(progress):
        return False, "❌ Рецепт ещё не открыт!"
    
    # ✅ ИСПРАВЛЕНО: spend_score НЕ async — убираем await!
    if score_manager:
        success, message = score_manager.spend_score(  # ← БЕЗ await!
            user_id=user_id,
            amount=cost_in_score,
            reason="alchemy_craft",
            context=item_id
        )
        if not success:
            return False, message
        progress["score_balance"] = max(0, progress.get("score_balance", 0) - cost_in_score)
    else:
        if current_balance < cost_in_score:
            return False, "❌ Недостаточно золотых!"
        progress["score_balance"] = current_balance - cost_in_score
    
    if item_id not in inventory:
        inventory.append(item_id)
        progress["inventory"] = inventory
    
    storage.save_user(user_id, progress)
    
    logger.info(f"⚗️ Пользователь {user_id} создал {item_id} за {cost_in_score} золотых")
    
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
            message += f"\nОтменить можно за {cancel_cost} золотых."
    
    message += "\n\n💡 Артефакт добавлен в инвентарь!"
    
    return message


async def handle_alchemy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback'ов алхимии — с комментарием Владимира!"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = query.data
    
    storage = context.bot_data.get('storage')
    score_manager = context.bot_data.get('score_manager')
    
    if not storage:
        await query.edit_message_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    if not (data == "back_to_game" or data.startswith("craft_")):
        return
    
    if data == "back_to_game":
        if query.message.photo:
            await query.edit_message_caption("Возвращаюсь в игру...")
        else:
            await query.edit_message_text("Возвращаюсь в игру...")
        return
    
    if data.startswith("craft_"):
        item_id = data[6:]
        all_items = get_all_items()
        
        if item_id not in all_items:
            error_msg = "❌ Артефакт не найден!"
            if query.message.photo:
                await query.edit_message_caption(error_msg)
            else:
                await query.edit_message_text(error_msg)
            return
        
        success, message = await execute_craft(int(user_id), item_id, storage, score_manager)
        
        if success:
            activation_message = get_alchemy_activation_message(item_id)
            
            # ✅ Владимир комментирует ТОЛЬКО если замок открыт
            progress = storage.get_user(int(user_id)) or {}
            if phrase_manager.is_castle_unlocked(progress):
                # Особые фразы для разных зелий
                if "madness" in item_id or "chaos" in item_id:
                    phrase = "«Зелье Безумия?.. Я уже приготовил совок... и смирительную рубашку на ваш размер.»"
                    mood = "relaxed"
                elif "bravery" in item_id:
                    phrase = "«Зелье Смелости?.. Надеюсь, вы знаете что делаете, сударыня.»"
                    mood = "approve"
                elif "dice" in item_id or "fate" in item_id:
                    phrase = "«Кубик Судьбы?.. Азарт — это интересно. Но помните: порядок не любит случайности.»"
                    mood = "thinking"
                else:
                    phrase = phrase_manager.get_vladimir_phrase("purchase_decoration").replace("🎩 ", "", 1)
                    mood = "approve"
                
                # ✅ ИСПОЛЬЗУЕМ send_character_message_by_id ДЛЯ КОЛЛБЭКОВ!
                await send_character_message_by_id(
                    user_id=user_id,
                    character="vladimir",
                    text=f"{phrase}\n\n{activation_message}",
                    mood=mood,
                    context=context
                )
            else:
                # Просто текст если замок закрыт
                if query.message.photo:
                    await query.edit_message_caption(activation_message, parse_mode="Markdown")
                else:
                    await query.edit_message_text(activation_message, parse_mode="Markdown")
        else:
            # Ошибка
            error_message = message
            if query.message.photo:
                await query.edit_message_caption(error_message, parse_mode="Markdown")
            else:
                await query.edit_message_text(error_message, parse_mode="Markdown")
        
        try:
            if not success or not phrase_manager.is_castle_unlocked(storage.get_user(int(user_id)) or {}):
                if query.message.photo:
                    await query.edit_message_caption("Готово!", parse_mode="Markdown")
                else:
                    await query.edit_message_text("Готово!", parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отредактировать сообщение: {e}")