"""
Обработчики боёв с боссами.
Версия: 2.1 (Vladimir First Meeting Trigger) 🗄️👑🎩

Интеграция:
- Все начисления очков через score_manager.add_score()
- Все списания через score_manager.spend_score()
- Автоматическое логирование в score_log
- ✅ Триггер первой встречи с Владимиром после победы над Финальным Владыкой
"""

import json
import os
import asyncio
import random
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from handlers.utils import load_json, send_character_message
from config import BOSS_DATA_DIR, BOSSES_INFO_FILE
from core.ui_helpers import get_persistent_keyboard

try:
    from handlers.effects_manager import calculate_modifiers
    from items import SHOP_ITEMS
except ImportError:
    def calculate_modifiers(user_id, storage=None):
        return {}
    SHOP_ITEMS = {}

bosses_data = load_json(BOSSES_INFO_FILE)


def escape_markdown_v2(text):
    escape_chars = r'_[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def get_boss_reward(boss_id):
    rewards_map = {
        "null_void": "звезда_сложения",
        "minus_shadow": "амулет_вычитания",
        "evil_multiplier": "мантия_умножения",
        "fracosaur": "щит_деления",
        "final_boss": "корона_матемага"
    }
    return rewards_map.get(boss_id, "звезда_сложения")


def unlock_new_zones(progress, boss_id):
    """Открывает новые зоны после победы над боссом"""
    unlocked = set(progress.get("unlocked_zones", ["addition"]))
    
    if boss_id == "null_void":
        unlocked.add("subtraction")
    elif boss_id == "minus_shadow":
        unlocked.add("multiplication")
    elif boss_id == "evil_multiplier":
        unlocked.add("division")
    elif boss_id == "fracosaur":
        unlocked.add("secret_level")
    elif boss_id == "final_boss":
        unlocked.add("time_world")
        unlocked.add("measure_world")
        unlocked.add("logic_world")
        unlocked.add("true_lord")
        
    progress["unlocked_zones"] = list(unlocked)
    
    zone_map = {
        "null_void": "addition",
        "minus_shadow": "subtraction",
        "evil_multiplier": "multiplication",
        "fracosaur": "division",
        "time_keeper": "time_world",
        "measure_keeper": "measure_world",
        "logic_keeper": "logic_world"
    }
    zone_id = zone_map.get(boss_id)
    if zone_id:
        completed_zones = set(progress.get("completed_zones", []))
        completed_zones.add(zone_id)
        completed_zones.add(f"boss_{boss_id}")
        progress["completed_zones"] = list(completed_zones)
    
    if boss_id == "final_boss":
        progress["completed_normal_game"] = True
    
    return progress


def check_ability_trigger(ability, is_correct, boss_health, task_idx, total_tasks):
    trigger = ability.get("trigger", "")
    if trigger == "при ошибке":
        return not is_correct
    elif trigger == "каждый ход":
        return True
    elif trigger == "когда HP ≤ 2":
        return boss_health <= 2
    elif trigger == "когда HP ≤ 3":
        return boss_health <= 3
    elif trigger == "за каждые 2 решённые задачи":
        return (task_idx + 1) % 2 == 0
    else:
        return False


def apply_boss_ability(user_id, boss_id, ability, progress, is_correct, score_manager=None):
    """
    Применяет способность босса.
    ✅ Теперь принимает score_manager для безопасного списания очков.
    """
    effect = ability.get("effect", "")
    current_balance = progress.get("score_balance", 0)
    boss_health = progress.get("boss_health", 5)
    selected_tasks = progress.get("selected_boss_tasks", [])
    task_idx = progress.get("boss_task_index", 0)
    used_abilities = progress.get("boss_abilities_used", [])
    
    # Вспомогательная функция для списания очков
    async def safe_spend(amount, reason, context):
        if score_manager:
            await score_manager.spend_score(user_id, amount, reason, context)
        else:
            progress["score_balance"] = max(0, progress.get("score_balance", 0) - amount)
    
    if "восстанавливает 1 HP" in effect:
        progress["boss_health"] = min(5, boss_health + 1)
        used_abilities.append(ability["name"])
    elif "удваивает текущее HP" in effect:
        if boss_health <= 2:
            progress["boss_health"] = min(5, boss_health * 2)
            used_abilities.append(ability["name"])
    elif "крадёт 5 очков" in effect:
        if not is_correct:
            asyncio.create_task(safe_spend(5, "boss_ability", f"{boss_id}_steal_5"))
            used_abilities.append(ability["name"])
    elif "крадёт до 10 очков" in effect:
        if not is_correct:
            stolen = min(10, current_balance)
            asyncio.create_task(safe_spend(stolen, "boss_ability", f"{boss_id}_steal_up_to_10"))
            progress["boss_health"] = min(5, boss_health + 1)
            used_abilities.append(ability["name"])
    elif "делит твои очки пополам" in effect:
        if not is_correct:
            penalty = current_balance // 2
            asyncio.create_task(safe_spend(penalty, "boss_ability", f"{boss_id}_halve"))
            used_abilities.append(ability["name"])
    elif "крадёт 15 очков" in effect:
        if not is_correct:
            asyncio.create_task(safe_spend(15, "boss_ability", f"{boss_id}_steal_15"))
            progress["boss_health"] = min(5, boss_health + 2)
            used_abilities.append(ability["name"])
    elif "удваивает количество оставшихся задач" in effect:
        remaining = len(selected_tasks) - task_idx
        new_tasks = selected_tasks[task_idx:task_idx + remaining]
        selected_tasks.extend(new_tasks)
        progress["selected_boss_tasks"] = selected_tasks
        used_abilities.append(ability["name"])
    elif "возвращает одну решённую задачу назад" in effect:
        if task_idx > 0:
            progress["boss_task_index"] = max(0, task_idx - 1)
            used_abilities.append(ability["name"])
    elif "пропускает следующую задачу" in effect:
        if task_idx < len(selected_tasks):
            progress["boss_task_index"] = task_idx + 1
            asyncio.create_task(safe_spend(20, "boss_ability", f"{boss_id}_skip_task"))
            used_abilities.append(ability["name"])
    elif "крадёт 25 очков" in effect:
        if boss_health <= 2:
            asyncio.create_task(safe_spend(25, "boss_ability", f"{boss_id}_steal_25"))
            progress["boss_health"] = min(5, boss_health + 2)
            used_abilities.append(ability["name"])
    elif "меняет единицы измерения" in effect:
        used_abilities.append(ability["name"])
    elif "добавляет ложную подсказку" in effect:
        used_abilities.append(ability["name"])
    elif "удваивает штрафы за ошибки" in effect:
        used_abilities.append(ability["name"])
    elif "крадёт до 20 очков" in effect:
        if not is_correct:
            stolen = min(20, current_balance)
            asyncio.create_task(safe_spend(stolen, "boss_ability", f"{boss_id}_steal_up_to_20"))
            progress["boss_health"] = min(5, boss_health + 1)
            used_abilities.append(ability["name"])
    elif "крадёт до 18 очков" in effect:
        if not is_correct:
            stolen = min(18, current_balance)
            asyncio.create_task(safe_spend(stolen, "boss_ability", f"{boss_id}_steal_up_to_18"))
            progress["boss_health"] = min(5, boss_health + 1)
            used_abilities.append(ability["name"])
    elif "делит твои очки на 1.5" in effect:
        if boss_health <= 2:
            penalty = int(current_balance / 1.5)
            asyncio.create_task(safe_spend(penalty, "boss_ability", f"{boss_id}_divide_1_5"))
            used_abilities.append(ability["name"])
    elif "крадёт 22 очка" in effect:
        if not is_correct:
            asyncio.create_task(safe_spend(22, "boss_ability", f"{boss_id}_steal_22"))
            progress["boss_health"] = min(5, boss_health + 2)
            used_abilities.append(ability["name"])
    elif "добавляет усложнение" in effect:
        used_abilities.append(ability["name"])
    elif "добавляет 2 дополнительные задачи" in effect:
        if boss_health <= 3:
            current_task = selected_tasks[task_idx]
            selected_tasks.insert(task_idx + 1, current_task)
            selected_tasks.insert(task_idx + 2, current_task)
            progress["selected_boss_tasks"] = selected_tasks
            used_abilities.append(ability["name"])
    elif "блокирует подсказки" in effect:
        used_abilities.append(ability["name"])
    elif "крадёт 30 очков" in effect:
        if not is_correct:
            asyncio.create_task(safe_spend(30, "boss_ability", f"{boss_id}_steal_30"))
            progress["boss_health"] = min(10, boss_health + 3)
            used_abilities.append(ability["name"])
    elif "перемешивает все оставшиеся задачи" in effect:
        remaining_tasks = selected_tasks[task_idx:]
        random.shuffle(remaining_tasks)
        selected_tasks = selected_tasks[:task_idx] + remaining_tasks
        progress["selected_boss_tasks"] = selected_tasks
        used_abilities.append(ability["name"])
    elif "активирует ФАЗУ 2" in effect:
        if boss_health <= 6:
            remaining = len(selected_tasks) - task_idx
            new_tasks = selected_tasks[task_idx:task_idx + remaining]
            selected_tasks.extend(new_tasks)
            progress["selected_boss_tasks"] = selected_tasks
            used_abilities.append(ability["name"])
    elif "применяет случайную способность" in effect:
        if boss_health <= 3:
            all_abilities = []
            for b_id, b_data in bosses_data.items():
                all_abilities.extend(b_data.get("abilities", []))
            if all_abilities:
                random_ability = random.choice(all_abilities)
                # Рекурсивный вызов с передачей score_manager
                apply_boss_ability(user_id, boss_id, random_ability, progress, is_correct, score_manager)
            used_abilities.append(ability["name"])
    elif "восстанавливает 2 HP каждый ход" in effect:
        if boss_health <= 6:
            progress["boss_health"] = min(10, boss_health + 2)
            used_abilities.append(ability["name"])
    
    progress["boss_abilities_used"] = used_abilities


MANUNYA_PHRASES_CORRECT = [
    "💬 **Манюня**: *«Так держать!»*",
    "💬 **Манюня**: *«Ты справишься!»*",
    "💬 **Манюня**: *«Вперёд к победе!»*",
    "💬 **Манюня**: *«Ты молодец!»*",
    "💬 **Манюня**: *«Продолжай в том же духе!»*"
]
MANUNYA_PHRASES_WRONG = [
    "💬 **Манюня**: *«Не сдавайся!»*",
    "💬 **Манюня**: *«У тебя всё получится!»*",
    "💬 **Манюня**: *«Попробуй ещё раз!»*",
    "💬 **Манюня**: *«Ошибки — это опыт!»*"
]
GEORGY_PHRASES_CORRECT = [
    "💚 **Слизень Георгий**: *«Ха! Босс дрожит!»*",
    "💚 **Слизень Георгий**: *«Ещё немного!»*",
    "💚 **Слизень Георгий**: *«Ты круче Владыки!»*"
]
GEORGY_PHRASES_WRONG = [
    "💚 **Слизень Георгий**: *«Ой-ой! Но мы не сдаёмся!»*",
    "💚 **Слизень Георгий**: *«Босс злится, а ты — решай!»*",
    "💚 **Слизень Георгий**: *«Ошибка? Ерунда! Вперёд!»*"
]


def load_boss_tasks(boss_id):
    if boss_id == "true_lord":
        return None
    boss_file = os.path.join(BOSS_DATA_DIR, f"{boss_id}.json")
    try:
        with open(boss_file, 'r', encoding='utf-8') as f:
            boss_data = json.load(f)
            return boss_data.get("tasks", [])
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Ошибка загрузки {boss_file}: {e}")
        return None


async def start_boss_battle(update: Update, context: ContextTypes.DEFAULT_TYPE, boss_id: str):
    user_id = update.effective_user.id if update.effective_user else 0
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    progress = storage.get_or_create_user(user_id, update.effective_user.username if update.effective_user else None)
    
    unlocked_zones = set(progress.get("unlocked_zones", ["addition"]))
    if boss_id == "null_void" and "addition" not in unlocked_zones:
        await update.message.reply_text("🔒 Сначала пройди Остров Сложения!")
        return
    elif boss_id == "minus_shadow" and "subtraction" not in unlocked_zones:
        await update.message.reply_text("🔒 Сначала победи Нуль-Пустоту!")
        return
    elif boss_id == "evil_multiplier" and "multiplication" not in unlocked_zones:
        await update.message.reply_text("🔒 Сначала победи Минус-Тень!")
        return
    elif boss_id == "fracosaur" and "division" not in unlocked_zones:
        await update.message.reply_text("🔒 Сначала победи Злого Умножителя!")
        return
    elif boss_id == "final_boss":
        required = {"subtraction", "multiplication", "division"}
        if not required.issubset(unlocked_zones):
            await update.message.reply_text("🔒 Победи всех боссов островов!")
            return
    
    all_tasks = load_boss_tasks(boss_id)
    if all_tasks is None:
        await update.message.reply_text(f"❌ Задачи для босса '{boss_id}' не найдены")
        return
    if not all_tasks:
        await update.message.reply_text(f"❌ Нет задач для босса '{boss_id}'")
        return
        
    selected_tasks = all_tasks.copy()
    random.shuffle(selected_tasks)
    
    max_health = 10 if boss_id == "true_lord" else 5
    progress.update({
        "in_boss_battle": True,
        "current_boss": boss_id,
        "selected_boss_tasks": selected_tasks,
        "boss_task_index": 0,
        "boss_health": max_health,
        "boss_abilities_used": [],
        "boss_turn": 0
    })
    storage.save_user(user_id, progress)

    boss_info = bosses_data.get(boss_id, {})
    boss_name = boss_info.get("name", "Босс")
    boss_description = boss_info.get("description", "")
    boss_emoji = boss_info.get("emoji", "👹")
    await send_character_message(update, boss_id, f"{boss_emoji} **{boss_name}**\n*{boss_description}*")

    dialogs = {
        "null_void": ("💬 **Манюня**: *«Осторожно! Нуль-Пустота может обнулить твои очки!»*", "💚 **Слизень Георгий**: *«Ха! Но мы умнее нуля!»*"),
        "minus_shadow": ("💬 **Манюня**: *«Минус-Тень вычитает твои силы!»*", "💚 **Слизень Георгий**: *«Но мы прибавим уверенности!»*"),
        "evil_multiplier": ("💬 **Манюня**: *«Злой Умножитель удваивает сложность!»*", "💚 **Слизень Георгий**: *«А мы умножим твою храбрость!»*"),
        "fracosaur": ("💬 **Манюня**: *«Дробозавр делит твои очки!»*", "💚 **Слизень Георгий**: *«Но мы соберём их в целое!»*"),
        "final_boss": ("💬 **Манюня**: *«Финальный Владыка — хозяин Числяндии!»*", "💚 **Слизень Георгий**: *«Покажем ему, кто тут главный!»*")
    }
    
    if boss_id in dialogs:
        manunya_msg, georgy_msg = dialogs[boss_id]
        await send_character_message(update, "manunya", manunya_msg)
        await asyncio.sleep(1.0)
        await send_character_message(update, "georgy", georgy_msg)
        await asyncio.sleep(1.2)
    
    task_text = escape_markdown_v2(selected_tasks[0]["question"])
    first_task = f"*{task_text}*"
    health_bar = "❤️" * max_health
    await update.message.reply_text(f"⚔️ **Задача 1**\nЗдоровье: {health_bar}\n\n❓ {first_task}", parse_mode="MarkdownV2", reply_markup=get_persistent_keyboard(progress, menu="boss_active"))


async def handle_boss_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else 0
    storage = context.bot_data.get('storage')
    score_manager = context.bot_data.get('score_manager')
    
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return False
    progress = storage.get_user(user_id)
    if not progress:
        return False
    if not progress.get("in_boss_battle", False):
        return False
        
    boss_id = progress.get("current_boss")
    if not boss_id:
        return False
        
    selected_tasks = progress.get("selected_boss_tasks", [])
    task_idx = progress.get("boss_task_index", 0)
    boss_health = progress.get("boss_health", 5)
    max_health = 10 if boss_id == "true_lord" else 5
    
    if task_idx >= len(selected_tasks) and boss_health > 0:
        random.shuffle(selected_tasks)
        progress["boss_task_index"] = 0
        progress["selected_boss_tasks"] = selected_tasks
        storage.save_user(user_id, progress)
        task_idx = 0
        
    if task_idx >= len(selected_tasks):
        return False
        
    current_task = selected_tasks[task_idx]
    text = update.message.text.strip().lower()
    
    if text in ["назад", "⬅️ назад", "выйти", "выход", "назад в игру"]:
        progress.update({
            "in_boss_battle": False,
            "current_boss": None,
            "selected_boss_tasks": [],
            "boss_task_index": 0,
            "boss_health": max_health,
            "boss_abilities_used": []
        })
        storage.save_user(user_id, progress)
        await update.message.reply_text("↩️ Вышла из боя!", reply_markup=get_persistent_keyboard(progress))
        return True
    
    if text in ["подсказка", "💡 подсказка"]:
        hint = current_task.get("hint", "Подсказки нет.")
        await update.message.reply_text(f"💡 {hint}")
        # ✅ СПИСАНИЕ ОЧКОВ ЧЕРЕЗ SCORE_MANAGER
        if score_manager:
            await score_manager.spend_score(user_id, 5, reason="hint_used", context=f"boss_{boss_id}")
        else:
            progress["score_balance"] = max(0, progress.get("score_balance", 0) - 5)
            storage.save_user(user_id, progress)
        return True
    
    try:
        answer = int(text)
    except ValueError:
        await update.message.reply_text("Нужно число!")
        return True
        
    # ✅ ИСПРАВЛЕНО: сравнение с допуском (хотя для int это не критично, но на будущее)
    expected = current_task["answer"]
    is_correct = abs(float(answer) - float(expected)) < 0.01
    
    progress["tasks_solved"] = progress.get("tasks_solved", 0) + 1
    if is_correct:
        progress["tasks_correct"] = progress.get("tasks_correct", 0) + 1
    
    boss_info = bosses_data.get(boss_id, {})
    abilities = boss_info.get("abilities", [])
    
    for ability in abilities:
        chance_str = ability.get("chance", "0%").replace("%", "")
        try:
            chance = int(chance_str)
        except ValueError:
            chance = 0
        if check_ability_trigger(ability, is_correct, boss_health, task_idx, len(selected_tasks)):
            if random.randint(1, 100) <= chance:
                # ✅ ПЕРЕДАЁМ score_manager В apply_boss_ability
                apply_boss_ability(user_id, boss_id, ability, progress, is_correct, score_manager)
                boss_messages = {
                    "null_void": "🌑 **Нуль\\-Пустота**: *«ХА\\-ХА! Я восстанавливаю силы!»*",
                    "minus_shadow": "🌑 **Минус\\-Тень**: *«Твои очки — мои!»*",
                    "evil_multiplier": "🌀 **Злой Умножитель**: *«Чем больше задач — тем веселее!»*",
                    "fracosaur": "🌊 **Дробозавр**: *«Половина твоих очков — моя!»*",
                    "final_boss": "👑 **Владыка**: *«Ты слаб!»*"
                }
                msg = boss_messages.get(boss_id, f"**{boss_info.get('name', 'Босс')}**: *«{ability['name']} активирована!»*")
                await send_character_message(update, boss_id, msg)
                await asyncio.sleep(1.0)
                break
    
    storage.save_user(user_id, progress)
    
    if is_correct:
        base_points = 20
        modifiers = calculate_modifiers(user_id, storage)
        point_multiplier = modifiers.get('point_multiplier', 1.0)
        bonus_points = modifiers.get('boss_win_bonus_points', 0)
        points_earned = int(base_points * point_multiplier) + bonus_points
        
        # ✅ НАЧИСЛЕНИЕ ЧЕРЕЗ SCORE_MANAGER
        if score_manager:
            await score_manager.add_score(
                user_id=user_id,
                amount=points_earned,
                reason="boss_task_correct",
                context=f"boss_{boss_id}_task_{task_idx}"
            )
        else:
            progress["score_balance"] = progress.get("score_balance", 0) + points_earned
            progress["total_score"] = progress.get("total_score", 0) + points_earned
        
        progress["boss_health"] = max(0, boss_health - 1)
        progress["boss_task_index"] = task_idx + 1
        await send_character_message(update, "manunya", random.choice(MANUNYA_PHRASES_CORRECT))
        await asyncio.sleep(0.8)
        await send_character_message(update, "georgy", random.choice(GEORGY_PHRASES_CORRECT))
    else:
        penalty = 15  # ✅ Положительное число для spend_score
        modifiers = calculate_modifiers(user_id, storage)
        
        if not modifiers.get('mistake_penalty_ignored', False):
            # ✅ СПИСАНИЕ ЧЕРЕЗ SCORE_MANAGER
            if score_manager:
                await score_manager.spend_score(
                    user_id=user_id,
                    amount=penalty,
                    reason="boss_task_wrong",
                    context=f"boss_{boss_id}_task_{task_idx}"
                )
            else:
                progress["score_balance"] = max(0, progress.get("score_balance", 0) - penalty)
        
        progress["boss_task_index"] = task_idx + 1
        await send_character_message(update, "manunya", random.choice(MANUNYA_PHRASES_WRONG))
        await asyncio.sleep(0.8)
        await send_character_message(update, "georgy", random.choice(GEORGY_PHRASES_WRONG))
    
    storage.save_user(user_id, progress)
    
    if progress["boss_health"] <= 0:
        # ✅ ПОБЕДА!
        reward = get_boss_reward(boss_id)
        progress["rewards"] = progress.get("rewards", [])
        progress["rewards"].append(reward)
        
        defeated_bosses = progress.get("defeated_bosses", [])
        if boss_id not in defeated_bosses:
            defeated_bosses.append(boss_id)
            progress["defeated_bosses"] = defeated_bosses
            
            # Достижения
            achievement_map = {
                "null_void": "zero_victory",
                "minus_shadow": "shadow_victory",
                "evil_multiplier": "multiply_victory",
                "fracosaur": "fracosaur_victory",
                "final_boss": "lord_victory"
            }
            ach_id = achievement_map.get(boss_id)
            if ach_id:
                achievements = progress.get("achievements", {})
                if not isinstance(achievements, dict):
                    achievements = {}
                achievements[ach_id] = True
                progress["achievements"] = achievements
            
            # ✅ ОТКРЫВАЕМ ЗОНЫ
            progress = unlock_new_zones(progress, boss_id)
            
            # ✅ ТРИГГЕР ПЕРВОЙ ВСТРЕЧИ С ВЛАДИМИРОМ (только для final_boss)
            if boss_id == "final_boss" and not progress.get("first_vladimir_meeting", False):
                from handlers.castle import trigger_vladimir_first_meeting
                await trigger_vladimir_first_meeting(user_id, context, storage)
                progress["first_vladimir_meeting"] = True
                storage.save_user(user_id, progress)
        
        storage.save_user(user_id, progress)
        
        await update.message.reply_text("🎉 **ПОБЕДА!**", parse_mode="Markdown")
        await send_character_message(update, "manunya", "✨ *УРААА!* Ты победила босса!")
        await asyncio.sleep(0.8)
        await send_character_message(update, "georgy", f"🥕 Ты получаешь: *{reward.replace('_', ' ').title()}*!")
        await asyncio.sleep(0.8)
        
        # ✅ ИСПРАВЛЕНА ОРФОГРАФИЯ
        zone_names_feminine = {
            "addition": "Остров Сложения",
            "subtraction": "Пещера Вычитания", 
            "multiplication": "Лес Умножения",
            "division": "Река Деления",
            "time_world": "Хронопия",
            "measure_world": "Мир Мер",
            "logic_world": "Мир Логики"
        }
        zone_map = {
            "null_void": "addition",
            "minus_shadow": "subtraction",
            "evil_multiplier": "multiplication",
            "fracosaur": "division",
            "time_keeper": "time_world",
            "measure_keeper": "measure_world",
            "logic_keeper": "logic_world"
        }
        zone_id = zone_map.get(boss_id)
        zone_name = zone_names_feminine.get(zone_id, "этот уровень")
        
        if zone_id in ["subtraction", "division"]:
            await update.message.reply_text(f"🏆 *{zone_name} полностью пройдена!*", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"🏆 *{zone_name} полностью пройден!*", parse_mode="Markdown")
        await asyncio.sleep(0.6)
        
        # ✅ АВТО-ЗАВЕРШЕНИЕ УРОВНЯ
        progress["current_level"] = None
        progress["selected_tasks"] = []
        progress["current_task_index"] = 0
        storage.save_user(user_id, progress)
        
        try:
            from handlers.levels import update_explorer_achievement
            progress = update_explorer_achievement(progress, zone_id or boss_id)
            storage.save_user(user_id, progress)
        except Exception:
            pass
    else:
        if progress["boss_task_index"] < len(selected_tasks):
            task_text = escape_markdown_v2(selected_tasks[progress["boss_task_index"]]["question"])
            next_task = f"*{task_text}*"
            task_num = progress["boss_task_index"] + 1
            health_bar = "❤️" * progress["boss_health"] + "💔" * (max_health - progress["boss_health"])
            await update.message.reply_text(
                f"⚔️ **Задача {task_num}**\nЗдоровье босса: {health_bar}\n\n❓ {next_task}",
                parse_mode="MarkdownV2",
                reply_markup=get_persistent_keyboard(progress, menu="boss_active")
            )
        else:
            await update.message.reply_text("❗ Босс слишком силён! Попробуй позже.")
            progress.update({
                "in_boss_battle": False,
                "current_boss": None,
                "selected_boss_tasks": [],
                "boss_task_index": 0,
                "boss_health": max_health,
                "boss_abilities_used": []
            })
            storage.save_user(user_id, progress)
            await update.message.reply_text("Выбери следующее приключение:", reply_markup=get_persistent_keyboard(progress))
        return True

    progress.update({
        "in_boss_battle": False,
        "current_boss": None,
        "selected_boss_tasks": [],
        "boss_task_index": 0,
        "boss_health": max_health,
        "boss_abilities_used": []
    })
    storage.save_user(user_id, progress)
    await update.message.reply_text("🎮 Выбери следующее приключение:", reply_markup=get_persistent_keyboard(progress))
    return True


# === КОМАНДЫ РАЗРАБОТЧИКА ===
async def dev_boss_null(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "null_void")
async def dev_boss_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "minus_shadow")
async def dev_boss_multiply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "evil_multiplier")
async def dev_boss_fracosaur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "fracosaur")
async def dev_boss_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "final_boss")
async def dev_boss_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "time_keeper")
async def dev_boss_measure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "measure_keeper")
async def dev_boss_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "logic_keeper")