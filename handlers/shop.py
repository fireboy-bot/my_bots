# handlers/shop.py
"""
Магазин предметов Числяндии.
Версия: 2.1 (Fix balance sync bug) 🗄️🛒💰🐛

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

logger = logging.getLogger(__name__)


def get_available_items(progress):
    """
    Возвращает список предметов, доступных для покупки.
    """
    unlocked_zones = set(progress.get("unlocked_zones", []))
    inventory = set(progress.get("inventory", []))
    
    available = []
    
    # --- ОСТРОВ СЛОЖЕНИЯ (доступен всегда) ---
    available.extend(["sum_gloves", "unity_stone"])
    
    # --- ОСТРОВ ВЫЧИТАНИЯ ---
    if "subtraction" in unlocked_zones:
        available.extend(["difference_dagger", "subtraction_shield", "ancient_amulet"])
    
    # --- УНИВЕРСАЛЬНЫЕ ПРЕДМЕТЫ ---
    available.extend(["accuracy_amulet", "magic_hat"])
    
    # --- СПЕЦИАЛЬНЫЕ ПРЕДМЕТЫ ---
    if progress.get("completed_normal_game", False):
        available.append("math_crown")
    
    # Убираем уже купленные (permanent) или уже активные (temporary)
    available = [item for item in available if item not in inventory]
    
    return available


def get_shop_inline_keyboard(available_items, current_balance):
    """Генерирует inline-кнопки ПОД сообщением"""
    keyboard = []
    
    for item_id in available_items:
        item = SHOP_ITEMS[item_id]
        cost = item.get("cost_in_score", 0)
        can_afford = current_balance >= cost
        
        if can_afford:
            button_text = f"🛒 Купить {item['name']} ({cost})"
            callback_data = f"buy_{item_id}"
        else:
            button_text = f"❌ {item['name']} ({cost}) — недоступно"
            callback_data = "noop"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Кнопка возврата
    keyboard.append([InlineKeyboardButton("⬅️ Назад в игру", callback_data="back_to_game")])
    
    return InlineKeyboardMarkup(keyboard)


async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    progress = storage.get_user(user_id) or {}
    
    available_items = get_available_items(progress)
    
    # ✅ ИСПРАВЛЕНО: используем score_balance как валюту
    current_balance = progress.get("score_balance", 0)
    total_rating = progress.get("total_score", 0)
    
    # Формируем подробный текст с описаниями
    shop_text = "🧙‍️ **ЛАВКА ЧИСЛЯНДИИ**\n\n"
    shop_text += f"💰 Твой баланс: *{current_balance} очков*\n"
    shop_text += f"🏆 Твой рейтинг: *{total_rating} очков*\n\n"
    shop_text += "Здесь ты можешь обменять очки на волшебные предметы!\n\n"
    
    # Добавляем список предметов с описаниями
    for item_id in available_items:
        item = SHOP_ITEMS[item_id]
        cost = item.get("cost_in_score", 0)
        can_afford = current_balance >= cost
        
        status = "✅" if can_afford else "❌"
        shop_text += f"{status} **{item['name']}**\n"
        shop_text += f"   💰 Цена: {cost} очков\n"
        shop_text += f"   ℹ️ {item['description']}\n\n"
    
    if not available_items:
        shop_text += "🔒 Нет доступных предметов.\n"
        shop_text += "Пройди больше островов, чтобы открыть новые артефакты!"
    else:
        shop_text += "📌 **Как купить?**\n"
        shop_text += "Нажми на кнопку под сообщением!"
    
    reply_markup = get_shop_inline_keyboard(available_items, current_balance)
    
    # ✅ ИСПРАВЛЕНО: путь через BASE_DIR
    image_path = os.path.join(BASE_DIR, 'images', 'shop_keeper.jpg')
    
    try:
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=shop_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        logger.warning(f"🖼️ Аватарка не найдена: {image_path}")
        await update.message.reply_text(
            shop_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"❌ Ошибка отправки магазина: {e}")
        await update.message.reply_text("⚠️ Ошибка загрузки магазина. Попробуй позже.")


async def execute_purchase(user_id: int, item_id: str, storage, score_manager=None) -> tuple[bool, str]:
    """
    Выполняет покупку предмета.
    
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
    
    if item_id not in SHOP_ITEMS:
        logger.error(f"❌ Предмет не найден в SHOP_ITEMS: {item_id}")
        return False, "❌ Предмет не найден!"
    
    item = SHOP_ITEMS[item_id]
    cost = item.get("cost_in_score", 0)
    item_type = item.get("type", "permanent")
    
    # Проверки
    if current_balance < cost:
        return False, f"❌ Недостаточно очков (нужно {cost}, есть {current_balance})!"
    
    # Для permanent-предметов: проверяем, не куплен ли уже
    if item_type == "permanent" and item_id in inventory:
        return False, "❌ Предмет уже куплен!"
    
    # Проверка доступности по зонам
    if item_id not in get_available_items(progress):
        return False, "❌ Предмет ещё не открыт!"
    
    # ✅ СПИСАНИЕ ОЧКОВ ЧЕРЕЗ SCORE_MANAGER
    if score_manager:
        success, message = await score_manager.spend_score(
            user_id=user_id,
            amount=cost,
            reason="shop_purchase",
            context=item_id
        )
        if not success:
            return False, message
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: обновляем локальный progress после spend_score
        # Чтобы финальный save_user() не перезаписал новый баланс старым значением
        progress["score_balance"] = max(0, progress.get("score_balance", 0) - cost)
    else:
        # Fallback: прямое списание (если score_manager не инициализирован)
        if current_balance < cost:
            return False, "❌ Недостаточно очков!"
        progress["score_balance"] = current_balance - cost
    
    # Добавляем предмет в инвентарь (только если не был куплен)
    if item_id not in inventory:
        inventory.append(item_id)
        progress["inventory"] = inventory
    
    # ✅ СОХРАНЯЕМ ЧЕРЕЗ PlayerStorage
    storage.save_user(user_id, progress)
    
    logger.info(f"🛒 Пользователь {user_id} купил {item_id} за {cost} очков")
    
    return True, f"✨ Куплено: {item['name']}!"


def get_item_activation_message(item_id: str) -> str:
    """Возвращает сообщение об активации эффекта предмета."""
    if item_id not in SHOP_ITEMS:
        return ""
    
    item = SHOP_ITEMS[item_id]
    item_name = item["name"]
    item_effect = item.get("effect")
    item_type = item.get("type")
    
    message = f"✨ Ты купила **{item_name}**!\n\n"
    
    if item_type == "permanent":
        message += "🔓 *Предмет добавлен в инвентарь навсегда!*\n\n"
        if item_effect == "hint_is_free":
            message += "🎯 *Эффект активирован!* Подсказки теперь бесплатны!"
        elif item_effect == "ignore_mistake_penalty":
            message += "🛡️ *Эффект активирован!* Ошибки больше не штрафуют!"
        elif item_effect == "multiply_points_by_x":
            message += "⭐ *Эффект активирован!* Очки за задачи умножаются!"
    elif item_type == "island_bound_temporary":
        message += "⏱️ *Эффект действует до конца острова!*\n\n"
        if item_effect == "additive_progressive":
            message += "🧤 *Эффект активирован!* За каждую задачу ты будешь получать больше очков!"
        elif item_effect == "perfect_run_bonus":
            message += "💎 *Эффект активирован!* Бонус за прохождение без ошибок!"
    
    message += "\n\n💡 Предмет работает автоматически!"
    
    return message


async def handle_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback'ов магазина."""
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
    
    # Обрабатываем ТОЛЬКО команды магазина
    if not (data == "back_to_game" or data.startswith("buy_")):
        return
    
    if data == "back_to_game":
        if query.message.photo:
            await query.edit_message_caption("Возвращаюсь в игру...")
        else:
            await query.edit_message_text("Возвращаюсь в игру...")
        return
    
    if data.startswith("buy_"):
        item_id = data[4:]
        
        success, message = await execute_purchase(user_id, item_id, storage, score_manager)
        
        if success:
            activation_message = get_item_activation_message(item_id)
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