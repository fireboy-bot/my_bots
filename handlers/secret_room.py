# handlers/secret_room.py
"""
Тайная Комната — пост-гейм модуль с исследованием, загадками и наградами.
Архитектура: handler → storage (без services/)
Версия: 1.11 (Content Loading Fix) 🗝️📚✅
"""

import random
import logging
import os
import json
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from core.ui_helpers import get_persistent_keyboard
from core.logger import log_user_action
from core.vladimir_profile import PlayerProfile

logger = logging.getLogger(__name__)

# Лимит попыток в день
SECRET_ROOM_MAX_ATTEMPTS = 3


# === 🧩 ЗАГРУЗКА ЗАДАЧ ИЗ ФАЙЛА ===

def _load_tasks_from_file() -> List[dict]:
    """Загружает задачи из файла."""
    tasks_file = os.path.join("data", "secret_room_tasks.json")
    if not os.path.exists(tasks_file):
        # Возвращаем заглушку если файла нет
        return [
            {"id": "p1", "question": "Сколько будет 7 × 8?", "options": ["54", "56", "64"], "correct": 1, "reward_points": 20, "reward_item": None, "explanation": "7 × 8 = 56"},
            {"id": "p2", "question": "Какое число следующее: 2, 4, 8, 16, ...?", "options": ["24", "32", "20"], "correct": 1, "reward_points": 20, "reward_item": None, "explanation": "×2"},
            {"id": "p3", "question": "Сколько углов у треугольника?", "options": ["2", "3", "4"], "correct": 1, "reward_points": 10, "reward_item": "ancient_coin", "explanation": "3 угла"},
            {"id": "p4", "question": "Что больше: половина от 100 или четверть от 200?", "options": ["Половина", "Четверть", "Одинаково"], "correct": 2, "reward_points": 20, "reward_item": None, "explanation": "50=50"},
            {"id": "p5", "question": "Сколько будет 100 − 37?", "options": ["63", "73", "53"], "correct": 0, "reward_points": 15, "reward_item": None, "explanation": "100-37=63"},
        ]
    
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_tasks = []
            for category in data.values():
                for task in category:
                    all_tasks.append({
                        "id": f"t{len(all_tasks)+1}",
                        "question": task["question"],
                        "options": [str(o) for o in task["options"]],
                        "correct": task["correct"],
                        "reward_points": task.get("reward", 10),
                        "reward_item": None,
                        "explanation": task.get("explanation", "")
                    })
            logger.info(f"✅ Загружено {len(all_tasks)} задач из {tasks_file}")
            return all_tasks
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки задач: {e}")
        return []

# Загружаем задачи при старте модуля
PUZZLES = _load_tasks_from_file()


# === 📜 БАЗА ЛОРА (заглушка — загрузится из файла) ===
LORE_ENTRIES = [
    "📜 Дневник Архитектора, день 1:\n«Сегодня я заложил первый камень Числяндии. Пусть числа ведут тех, кто ищет истину.»",
    "📜 Запись в древнем фолианте:\n«Тот, кто постигнет сложение, откроет врата. Тот, кто освоит умножение — обретёт силу.»",
    "📜 Письмо от прошлого игрока:\n«Я думал, что 7×8=54... Владимир был недоволен. Но я исправился!»",
    "📜 Легенда о Финальном Владыке:\n«Он правил числами, но забыл, что порядок рождается из понимания, а не из страха.»",
    "📜 Заметка на полях учебника:\n«Ошибка — это не провал. Это шаг к правильному ответу. — Манюня»"
]


# === 💎 БАЗА ПРЕДМЕТОВ ===
SECRET_ITEMS = {
    "ancient_coin": "🪙 Древняя монета — артефакт первых дней Числяндии",
    "crystal_shard": "💎 Осколок кристалла — светится при правильных ответах",
    "logic_key": "🗝️ Ключ логики — открывает скрытые пути",
    "wisdom_scroll": "📜 Свиток мудрости — даёт подсказку в бою с боссом"
}


# === 🎲 ВЕСА СОБЫТИЙ ===
EVENT_WEIGHTS = {
    "puzzle": 40,
    "reward": 30,
    "lore": 20,
    "empty": 10
}


# === 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _get_user_secret_data(user_data: dict) -> dict:
    """Безопасно получает данные Тайной комнаты из user_data."""
    return {
        "level": user_data.get("secret_room_level", 1),
        "exp": user_data.get("secret_room_exp", 0),
        "items": user_data.get("secret_room_items", []),
        "logs": user_data.get("secret_room_logs", []),
        "last_event": user_data.get("secret_room_last_event", None)
    }


def _save_user_secret_data(user_data: dict, secret_data: dict, storage, user_id: str):
    """Сохраняет обновлённые данные Тайной комнаты."""
    user_data["secret_room_level"] = secret_data.get("level", 1)
    user_data["secret_room_exp"] = secret_data.get("exp", 0)
    user_data["secret_room_items"] = secret_data.get("items", [])
    user_data["secret_room_logs"] = secret_data.get("logs", [])
    user_data["secret_room_last_event"] = secret_data.get("last_event")


def _get_exp_for_next_level(level: int) -> int:
    """Возвращает количество опыта для следующего уровня."""
    return 50 * (2 ** (level - 1))


def _check_level_up(secret_data: dict) -> tuple:
    """Проверяет и выполняет повышение уровня."""
    current_level = secret_data.get("level", 1)
    current_exp = secret_data.get("exp", 0)
    exp_needed = _get_exp_for_next_level(current_level)
    
    if current_exp >= exp_needed:
        secret_data["level"] = current_level + 1
        secret_data["exp"] = 0
        new_level = secret_data["level"]
        next_exp = _get_exp_for_next_level(new_level)
        message = f"🎉 <b>УРОВЕНЬ ПОВЫШЕН!</b>\n🗝️ Тайная комната: Уровень {new_level}\n✨ Опыт: 0/{next_exp}"
        return True, message
    return False, ""


def _roll_event() -> str:
    """Случайное событие с весами."""
    events = list(EVENT_WEIGHTS.keys())
    weights = list(EVENT_WEIGHTS.values())
    return random.choices(events, weights=weights, k=1)[0]


def _generate_puzzle_keyboard(question_id: str, options: list) -> InlineKeyboardMarkup:
    """Генерирует inline-кнопки для загадки."""
    keyboard = []
    for idx, option in enumerate(options):
        callback = f"secret_answer_{question_id}_{idx}"
        keyboard.append([InlineKeyboardButton(option, callback_data=callback)])
    return InlineKeyboardMarkup(keyboard)


def _add_reward(user_data: dict, secret_data: dict, points: int, item: str = None) -> tuple:
    """Добавляет награду пользователю."""
    messages = []
    
    if points > 0:
        current_balance = user_data.get("score_balance", 0)
        user_data["score_balance"] = current_balance + points
        secret_data["exp"] = secret_data.get("exp", 0) + points
        messages.append(f"✨ +{points} очков!")
    
    if item and item not in secret_data.get("items", []):
        secret_data.setdefault("items", []).append(item)
        item_name = SECRET_ITEMS.get(item, item)
        messages.append(f"🎁 Получено: {item_name}")
    
    leveled_up, level_message = _check_level_up(secret_data)
    if leveled_up:
        messages.append(level_message)
    
    return " ".join(messages) if messages else "", leveled_up, level_message


def _load_lore_from_file() -> List[dict]:
    """Загружает лор из файла если существует."""
    lore_file = os.path.join("data", "secret_lore.json")
    if not os.path.exists(lore_file):
        return []
    
    try:
        with open(lore_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("lore_entries", [])
    except:
        return []


# === 🎮 ОСНОВНЫЕ ХЕНДЛЕРЫ ===

async def enter_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вход в Тайную комнату — с проверкой ежедневного доступа."""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    # ✅ ЧИТАЕМ СВЕЖИЕ ДАННЫЕ ИЗ БД
    user_data = storage.get_user(user_id) or {}
    profile = PlayerProfile(user_data)
    
    # Проверяем статус доступа
    status = profile.get_secret_room_status()
    
    logger.info(f"🔍 Тайная комната: user_id={user_id}, attempts_left={status['attempts_left']}, streak={status['streak']}")
    
    # 🔒 ЕСЛИ НЕДОСТУПНО — показываем экран «вернись завтра»
    if not status["available"]:
        msg = (
            "🗝️ <b>ТАЙНАЯ КОМНАТА</b>\n\n"
            "🔒 Комната закрыта до следующего ритуала.\n\n"
            f"⏳ Откроется через: {status['resets_at']}\n"
            f"🔥 Твоя серия: {status['streak']} дней!\n"
            f"📊 Всего посещений: {status['total_visits']}\n\n"
            "💡 Совет: Завтра может выпасть РЕДКИЙ артефакт..."
        )
        
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("⬅️ Назад")]],
            resize_keyboard=True
        )
        
        await adapter.send_message(
            user_id=user_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # ✅ ЕСЛИ ДОСТУПНО — показываем меню с лимитом попыток
    secret_data = _get_user_secret_data(user_data)
    exp_needed = _get_exp_for_next_level(secret_data['level'])
    
    msg = (
        "🗝️ <b>ТАЙНАЯ КОМНАТА</b>\n\n"
        f"📊 Уровень: {secret_data['level']}\n"
        f"✨ Опыт: {secret_data['exp']}/{exp_needed}\n"
        f"🎁 Попыток сегодня: {status['attempts_left']}/{SECRET_ROOM_MAX_ATTEMPTS}\n"
        f"🔥 Серия: {status['streak']} дней!\n"
        f"📜 Записей в дневнике: {len(secret_data['logs'])}\n\n"
        "Выберите действие:"
    )
    
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔍 Исследовать"), KeyboardButton("📜 Дневники")],
            [KeyboardButton("💎 Коллекция"), KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    log_user_action(user_id, "SECRET_ROOM_ENTER")


async def explore_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Механика "Исследовать" — с ПЕРЕЧТЕНИЕМ из БД."""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    # ✅ ЧИТАЕМ СВЕЖИЕ ДАННЫЕ ИЗ БД ПЕРЕД ПРОВЕРКОЙ!
    user_data = storage.get_user(user_id) or {}
    profile = PlayerProfile(user_data)
    status = profile.get_secret_room_status()
    
    logger.info(f"🔍 explore_secret_room: user_id={user_id}, attempts_left={status['attempts_left']}")
    
    # 🔒 ПРОВЕРКА: есть ли попытки
    if status["attempts_left"] <= 0:
        logger.warning(f"⚠️ Попытки исчерпаны! user_id={user_id}")
        await adapter.send_message(
            user_id=user_id,
            text=(
                "⚠️ <b>Ты исчерпал попытки на сегодня!</b>\n\n"
                f"🔒 Комната откроется через: {status['resets_at']}\n"
                f"🔥 Твоя серия: {status['streak']} дней\n\n"
                "💡 Завтра ждёт новый лор и новые загадки!"
            ),
            parse_mode="HTML"
        )
        return
    
    secret_data = _get_user_secret_data(user_data)
    event_type = _roll_event()
    secret_data["last_event"] = event_type
    
    level_up_message = ""
    lore_seen = []
    
    if event_type == "puzzle":
        await _handle_puzzle_event(update, context, user_id, user_data, secret_data, storage)
    elif event_type == "reward":
        reward_text, leveled_up, lvl_msg = _add_reward(user_data, secret_data, random.choice([10, 15, 20]))
        if leveled_up:
            level_up_message = lvl_msg
        msg = f"✨ <b>НАЙДЕНО!</b>\n\n{reward_text}\n\nПродолжай исследовать!"
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("🔍 Исследовать ещё"), KeyboardButton("⬅️ Назад")]],
            resize_keyboard=True
        )
        await adapter.send_message(
            user_id=user_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        log_user_action(user_id, "SECRET_REWARD")
    elif event_type == "lore":
        all_lore = _load_lore_from_file()
        if all_lore:
            seen = set(profile.profile.get("lore_seen", []))
            available = [l for l in all_lore if l["id"] not in seen]
            if available:
                lore_entry = random.choice(available)
                lore_seen.append(lore_entry["id"])
                lore_text = f"📜 {lore_entry.get('title', 'Запись')}\n\n{lore_entry['text']}"
            else:
                lore_text = random.choice(LORE_ENTRIES)
        else:
            lore_text = random.choice(LORE_ENTRIES)
        
        if lore_text not in secret_data.get("logs", []):
            secret_data.setdefault("logs", []).append(lore_text)
        
        msg = f"📜 <b>НАЙДЕНА ЗАПИСЬ</b>\n\n{lore_text}\n\nДобавлено в дневник!"
        
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("🔍 Исследовать ещё"), KeyboardButton("📜 Мой дневник"), KeyboardButton("⬅️ Назад")]],
            resize_keyboard=True
        )
        
        await adapter.send_message(
            user_id=user_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        log_user_action(user_id, "SECRET_LORE")
    else:
        await _handle_empty_event(update, context, user_id, user_data, secret_data, storage)
    
    # ✅ ОТСЛЕЖИВАЕМ ПОСЕЩЕНИЕ (увеличивает attempts_today)
    profile.track_secret_room_visit(lore_seen=lore_seen)
    
    # ✅ СОХРАНЯЕМ ДАННЫЕ
    _save_user_secret_data(user_data, secret_data, storage, user_id)
    storage.save_user(user_id, user_data)
    
    logger.info(f"✅ Сохранено: attempts_today={profile.profile['secret_room']['attempts_today']}")
    
    # ✅ ПОКАЗЫВАЕМ СООБЩЕНИЕ О ПОВЫШЕНИИ УРОВНЯ
    if level_up_message:
        await adapter.send_message(
            user_id=user_id,
            text=level_up_message,
            parse_mode="HTML"
        )
        log_user_action(user_id, "SECRET_LEVEL_UP")


async def _handle_puzzle_event(update, context, user_id: str, user_data: dict, secret_data: dict, storage):
    """Событие: загадка."""
    adapter = context.bot_data.get('adapter')
    puzzle = random.choice(PUZZLES)
    
    msg = f"🧩 <b>ЗАГАДКА</b>\n\n{puzzle['question']}\n\nВыберите ответ:"
    keyboard = _generate_puzzle_keyboard(puzzle["id"], puzzle["options"])
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def _handle_empty_event(update, context, user_id: str, user_data: dict, secret_data: dict, storage):
    """Событие: пусто."""
    adapter = context.bot_data.get('adapter')
    
    empty_messages = [
        "🔍 Ты осмотрелся... пока ничего интересного.",
        "🕯️ Пыль и тишина. Попробуй ещё раз!",
        "🗝️ Комната хранит секреты.",
        "✨ Что-то шевельнулось... но исчезло.",
    ]
    
    msg = random.choice(empty_messages)
    
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("🔍 Исследовать ещё"), KeyboardButton("⬅️ Назад")]],
        resize_keyboard=True
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def show_secret_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать дневник с прогрессом коллекции."""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    user_data = storage.get_user(user_id) or {}
    profile = PlayerProfile(user_data)
    secret_data = _get_user_secret_data(user_data)
    
    logs = secret_data.get("logs", [])
    completion = profile.get_lore_completion()
    
    if not logs:
        msg = (
            "📜 <b>ДНЕВНИК ПУСТ</b>\n\n"
            f"🔍 Исследуй Тайную комнату чтобы найти записи!\n"
            f"📊 Прогресс коллекции: {completion['seen']}/{completion['total']} ({completion['percent']}%)"
        )
    else:
        msg = (
            f"📜 <b>ТВОЙ ДНЕВНИК</b> ({len(logs)} записей)\n\n"
            f"📊 Коллекция: {completion['seen']}/{completion['total']} ({completion['percent']}%)\n\n"
        )
        for idx, entry in enumerate(logs[-5:], 1):
            msg += f"{idx}. {entry}\n\n"
        
        if completion['reward_unlocked']:
            msg += "🎉 <b>КОЛЛЕКЦИЯ СОБРАНА!</b>\n💎 Награда: уникальный артефакт!\n\n"
    
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔍 Исследовать"), KeyboardButton("💎 Коллекция")],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def show_secret_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать предметы."""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    user_data = storage.get_user(user_id) or {}
    secret_data = _get_user_secret_data(user_data)
    
    items = secret_data.get("items", [])
    
    if not items:
        msg = "💎 <b>КОЛЛЕКЦИЯ ПУСТА</b>\n\nИсследуй чтобы найти артефакты!"
    else:
        msg = f"💎 <b>ТВОИ АРТЕФАКТЫ</b> ({len(items)})\n\n"
        for item_id in items:
            item_desc = SECRET_ITEMS.get(item_id, f"📦 {item_id}")
            msg += f"• {item_desc}\n"
    
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔍 Исследовать"), KeyboardButton("📜 Дневники")],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню."""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    keyboard = get_persistent_keyboard(user_data, menu="main")
    
    await adapter.send_message(
        user_id=user_id,
        text="🏰 <b>ГЛАВНОЕ МЕНЮ</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def handle_secret_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответов на загадки."""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    data = query.data
    if not data.startswith("secret_"):
        return
    
    if data == "secret_explore":
        await explore_secret_room(update, context)
        return
    elif data == "secret_back":
        await back_to_menu(update, context)
        return
    
    if not data.startswith("secret_answer_"):
        return
    
    parts = data.split("_")
    if len(parts) != 4:
        await query.edit_message_text("⚠️ Ошибка.")
        return
    
    question_id = parts[2]
    try:
        selected_idx = int(parts[3])
    except ValueError:
        await query.edit_message_text("⚠️ Ошибка.")
        return
    
    puzzle = next((p for p in PUZZLES if p["id"] == question_id), None)
    if not puzzle:
        await query.edit_message_text("❌ Загадка не найдена.")
        return
    
    is_correct = (selected_idx == puzzle["correct"])
    
    adapter = context.bot_data.get('adapter')
    storage = context.bot_data.get('storage')
    
    if adapter:
        user_id = adapter.normalize_user_id(query.from_user.id)
    else:
        user_id = str(query.from_user.id)
    
    if storage:
        user_data = storage.get_user(user_id) or {}
        secret_data = _get_user_secret_data(user_data)
        
        if is_correct:
            points = puzzle.get("reward_points", 10)
            item = puzzle.get("reward_item")
            reward_text, leveled_up, level_message = _add_reward(user_data, secret_data, points, item)
            msg = f"✅ <b>ПРАВИЛЬНО!</b>\n\n{puzzle['explanation']}\n\n{reward_text}"
        else:
            correct_option = puzzle["options"][puzzle["correct"]]
            msg = f"❌ <b>Не совсем...</b>\n\nПравильный ответ: {correct_option}\n💡 {puzzle['explanation']}"
            secret_data["exp"] = secret_data.get("exp", 0) + 1
        
        _save_user_secret_data(user_data, secret_data, storage, user_id)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Исследовать ещё", callback_data="secret_explore")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="secret_back")]
        ])
        
        try:
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            await query.message.reply_text(msg, reply_markup=keyboard, parse_mode="HTML")
    else:
        await query.edit_message_text("⚠️ Ошибка: хранилище.")
    
    log_user_action(user_id, "SECRET_PUZZLE_ANSWER", f"correct={is_correct}")


def get_secret_room_handlers():
    """Возвращает список хендлеров."""
    return [
        MessageHandler(filters.Text("🗝️ Тайная Комната") & ~filters.COMMAND, enter_secret_room),
        MessageHandler(filters.Text("🔍 Исследовать") & ~filters.COMMAND, explore_secret_room),
        MessageHandler(filters.Text("🔍 Исследовать ещё") & ~filters.COMMAND, explore_secret_room),
        MessageHandler(filters.Text("📜 Дневники") & ~filters.COMMAND, show_secret_logs),
        MessageHandler(filters.Text("📜 Мой дневник") & ~filters.COMMAND, show_secret_logs),
        MessageHandler(filters.Text("💎 Коллекция") & ~filters.COMMAND, show_secret_items),
        MessageHandler(filters.Text("⬅️ Назад") & ~filters.COMMAND, back_to_menu),
        CallbackQueryHandler(handle_secret_answer_callback, pattern="^secret_"),
    ]


__all__ = [
    "enter_secret_room",
    "explore_secret_room",
    "show_secret_logs",
    "show_secret_items",
    "back_to_menu",
    "handle_secret_answer_callback",
    "get_secret_room_handlers",
]