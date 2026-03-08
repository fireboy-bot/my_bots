# handlers/levels.py
"""
Обработчики уровней (острова и миры).
Версия: 2.5 (Fix: sync progress after add_score) 🎮💡⬅️🛡️
"""

import json
import os
import asyncio
import random
from telegram import Update
from telegram.ext import ContextTypes
from handlers.utils import load_json, send_character_message
from config import TASKS_FILE, SHARDS_FILE, WORLD_DATA_DIR

from core.ui_helpers import get_game_keyboard, get_persistent_keyboard

try:
    from handlers.effects_manager import calculate_modifiers
    from items import SHOP_ITEMS
except ImportError:
    def calculate_modifiers(user_id, storage=None):
        return {}
    SHOP_ITEMS = {}


def get_health_bar(current: int, max: int = 5) -> str:
    filled = "❤️" * current
    empty = "💔" * (max - current)
    return f"{filled}{empty}"


def load_world_tasks(world_id):
    world_file = os.path.join(WORLD_DATA_DIR, f"{world_id}.json")
    try:
        with open(world_file, 'r', encoding='utf-8') as f:
            world_data = json.load(f)
            return world_data.get("tasks", [])
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Ошибка загрузки {world_file}: {e}")
        return None


async def enter_level(update: Update, context: ContextTypes.DEFAULT_TYPE, level_id: str):
    user_id = update.effective_user.id if update.effective_user else 0
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    progress = storage.get_user(user_id) or {}
    
    island_themes = {
        "addition": {"emoji": "🌅", "title": "🌅 **ОСТРОВ СЛОЖЕНИЯ**", "intro": "Ты ступаешь на солнечный берег, где волны шепчут: *«Сложи нас вместе!»* 🌊✨", "manunya": "💬 **Манюня**: *«Собери ракушки по две — и море улыбнётся!»*"},
        "subtraction": {"emoji": "🌑", "title": "🌑 **ПЕЩЕРА ВЫЧИТАНИЯ**", "intro": "Тёмный тоннель открывается перед тобой. Капли воды *кап-кап* отсчитывают уходящее время... 💧", "manunya": "💬 **Манюня**: *«Не бойся темноты — каждый шаг вперёд делает её светлее!»*"},
        "multiplication": {"emoji": "🌳", "title": "🌳 **ЛЕС УМНОЖЕНИЯ**", "intro": "Деревья растут парами, тройками, десятками! Ветви шепчут: *«Раз, два, три — и целый лес!»* 🍃", "manunya": "💬 **Манюня**: *«Одно семечко → целое дерево! Так работает волшебство умножения!»*"},
        "division": {"emoji": "🌊", "title": "🌊 **РЕКА ДЕЛЕНИЯ**", "intro": "Река разделяет камни на равные части. Волны напевают: *«Поровну для всех!»* 💧", "manunya": "💬 **Манюня**: *«Дели с друзьями — и радость умножится!»*"},
        "time_world": {"emoji": "🕒", "title": "🕒 **МИР ВРЕМЕНИ**", "intro": "Песок в часах пересыпается... Каждая секунда — новая загадка! ⏳", "manunya": "💬 **Манюня**: *«Время — величайшая загадка!»*"},
        "measure_world": {"emoji": "📏", "title": "📏 **МИР МЕР**", "intro": "Здесь даже пылинка имеет свой вес, а листок — свою длину! Всё можно измерить! ⚖️", "manunya": "💬 **Манюня**: *«Здесь даже пылинка имеет свой вес!»*"},
        "logic_world": {"emoji": "🧠", "title": "🧠 **МИР ЛОГИКИ**", "intro": "Лабиринты мыслей раскрываются перед тобой. Каждая задача — головоломка! 🔍", "manunya": "💬 **Манюня**: *«Здесь каждая задача — головоломка!»*"}
    }
    
    theme = island_themes.get(level_id, island_themes["addition"])
    
    await update.message.reply_text(theme["title"], parse_mode="Markdown")
    await asyncio.sleep(0.6)
    await update.message.reply_text(theme["intro"], parse_mode="Markdown")
    await asyncio.sleep(0.6)
    await send_character_message(update, "manunya", theme["manunya"])
    await asyncio.sleep(0.5)
    
    all_tasks = load_world_tasks(level_id)
    if not all_tasks:
        await update.message.reply_text(
            "⚠️ Нет задач для этого уровня!",
            reply_markup=get_game_keyboard()
        )
        return
    
    num_tasks = 20 if level_id in ["time_world", "measure_world", "logic_world"] else 10
    selected_tasks = random.sample(all_tasks, min(num_tasks, len(all_tasks)))
    progress.update({
        "current_level": level_id,
        "selected_tasks": selected_tasks,
        "current_task_index": 0,
        "in_boss_battle": False,
        "in_secret_level": False,
        "mistakes_in_level": 0
    })
    storage.save_user(user_id, progress)
    
    first_task = selected_tasks[0]["question"]
    task_text = (
        f"{theme['emoji']} *ЗАДАЧА 1 из {len(selected_tasks)}*\n"
        f"{'━' * 10}\n"
        f"❓ *{first_task}*\n"
        f"{'━' * 10}"
    )
    
    await update.message.reply_text(
        task_text,
        parse_mode="Markdown",
        reply_markup=get_game_keyboard()
    )


async def handle_level_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    text = update.message.text.strip()
    user_text = text.lower()
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    score_manager = context.bot_data.get('score_manager')
    
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return False
    
    progress = storage.get_user(user_id) or {}
    current_level = progress.get("current_level")
    if not current_level:
        return False
    
    selected_tasks = progress.get("selected_tasks", [])
    task_idx = progress.get("current_task_index", 0)
    
    if task_idx >= len(selected_tasks):
        await update.message.reply_text("Уровень завершён!")
        progress.update({"current_level": None, "selected_tasks": [], "current_task_index": 0})
        storage.save_user(user_id, progress)
        await update.message.reply_text("🎮 Выбери следующее приключение:", reply_markup=get_persistent_keyboard(progress))
        return True
    
    if user_text in ["назад", "⬅️ назад", "выйти", "выход", "назад в игру"]:
        progress.update({"current_level": None, "selected_tasks": [], "current_task_index": 0, "mistakes_in_level": 0})
        storage.save_user(user_id, progress)
        await update.message.reply_text("↩️ Вышла из уровня!", reply_markup=get_persistent_keyboard(progress))
        return True
    
    if user_text in ["💡 подсказка", "подсказка"]:
        hint = selected_tasks[task_idx].get("hint", "Подумай внимательнее!")
        await update.message.reply_text(f"💡 *{hint}*", parse_mode="Markdown")
        modifiers = calculate_modifiers(user_id, storage)
        if not modifiers.get('hint_is_free', False):
            if score_manager:
                score_manager.spend_score(user_id, 5, reason="hint_used", context=f"level_{current_level}")
            else:
                progress["score_balance"] = max(0, progress.get("score_balance", 0) - 5)
                storage.save_user(user_id, progress)
        current_task = selected_tasks[task_idx]["question"]
        emoji_map = {"addition": "🌅", "subtraction": "🌑", "multiplication": "🌳", "division": "🌊", "time_world": "🕒", "measure_world": "📏", "logic_world": "🧠"}
        emoji = emoji_map.get(current_level, "❓")
        task_text = (f"{emoji} *ЗАДАЧА {task_idx + 1} из {len(selected_tasks)}*\n{'━' * 10}\n❓ *{current_task}*\n{'━' * 10}")
        await update.message.reply_text(task_text, parse_mode="Markdown", reply_markup=get_game_keyboard())
        return True
    
    island_buttons = ["➕ сложение", "➖ вычитание", "✖️ умножение", "➗ деление", "🗺️ мир", "🏝️ острова", "⚔️ боссы", "📊 прогресс", "🎒 инвентарь", "➕ продолжить сложение", "➖ продолжить вычитание", "✖️ продолжить умножение", "➗ продолжить деление"]
    if any(btn in user_text for btn in island_buttons):
        await update.message.reply_text("⚠️ Сначала заверши текущий уровень или нажми *Назад*!", parse_mode="Markdown")
        return True
    
    try:
        text_normalized = text.replace(',', '.')
        answer = float(text_normalized)
        
        if not selected_tasks or task_idx >= len(selected_tasks):
            await update.message.reply_text("🎉 Уровень завершён! Возвращаюсь в меню.")
            progress.update({"current_level": None, "selected_tasks": [], "current_task_index": 0})
            storage.save_user(user_id, progress)
            from core.ui_helpers import get_persistent_keyboard
            await update.message.reply_text("🎮 Выбери следующее приключение:", reply_markup=get_persistent_keyboard(progress))
            return True
        
        expected_answer = float(selected_tasks[task_idx]["answer"])
        is_correct = abs(answer - expected_answer) < 0.01
        
        progress["tasks_solved"] = progress.get("tasks_solved", 0) + 1
        if is_correct:
            progress["tasks_correct"] = progress.get("tasks_correct", 0) + 1
        storage.save_user(user_id, progress)
        
        if is_correct:
            progress["current_task_index"] = task_idx + 1
            modifiers = calculate_modifiers(user_id, storage)
            
            base_score = 50
            point_multiplier = modifiers.get('point_multiplier', 1.0)
            progressive_bonus = modifiers.get('progressive_score_bonus', 0)
            
            earned_score = int(base_score * point_multiplier)
            
            bonus_messages = []
            
            if current_level == "addition" and progressive_bonus > 0:
                earned_score += progressive_bonus
                bonus_messages.append(f"🧤 +{progressive_bonus}")
            
            if modifiers.get('double_equal_operands', False):
                question = selected_tasks[task_idx]["question"]
                if "+" in question:
                    parts = question.split("+")
                    if len(parts) == 2 and parts[0].strip() == parts[1].strip():
                        earned_score *= 2
                        bonus_messages.append("💎 ×2")
            
            if bonus_messages:
                bonus_text = " + ".join(bonus_messages)
                await update.message.reply_text(f"✨ *БОНУСЫ:* {bonus_text}\n💰 +{earned_score} очков!", parse_mode="Markdown")
                await asyncio.sleep(0.5)
            
            # ✅ НАЧИСЛЕНИЕ ЧЕРЕЗ SCORE_MANAGER + СИНХРОНИЗАЦИЯ progress
            if score_manager:
                score_manager.add_score(
                    user_id=user_id,
                    amount=earned_score,
                    reason="level_task_correct",
                    context=f"level_{current_level}_task_{task_idx}"
                )
                # ✅ ОБНОВЛЯЕМ progress с новыми значениями из БД
                progress["total_score"] = progress.get("total_score", 0) + earned_score
                progress["score_balance"] = progress.get("score_balance", 0) + earned_score
            
            # XP
            base_xp = 10
            xp_bonus = modifiers.get('xp_bonus_per_task', 0)
            xp_multiplier = modifiers.get('xp_multiplier', 1.0)
            earned_xp = int((base_xp + xp_bonus) * xp_multiplier)
            
            current_xp = progress.get("xp", 0) + earned_xp
            current_level_num = progress.get("level", 1)
            xp_to_next = progress.get("xp_to_next", 50)
            while current_xp >= xp_to_next:
                current_xp -= xp_to_next
                current_level_num += 1
                xp_to_next = 50 + (current_level_num - 1) * 10
                await update.message.reply_text(f"🎉 *ПОЗДРАВЛЯЕМ!* Ты достигла уровня {current_level_num}!", parse_mode="Markdown")
            progress.update({"xp": current_xp, "level": current_level_num, "xp_to_next": xp_to_next})
            storage.save_user(user_id, progress)
            
            positive_phrases = [("✨ *Ура!* Ты справилась!", "manunya"), ("🌟 *Отлично!* Числа танцуют от радости!", "georgy"), ("🎉 *Молодец!* Манюня хлопает в ладоши!", "manunya"), ("💖 *Правильно!* Даже Слизень Георгий улыбнулся!", "georgy"), ("🌈 *Вау!* Ты — настоящий матемаг!", "manunya")]
            phrase, character = random.choice(positive_phrases)
            await send_character_message(update, character, phrase)
            await asyncio.sleep(0.7)
            
            if task_idx + 1 >= len(selected_tasks):
                await _complete_level(update, context, progress, user_id, current_level, storage, score_manager)
            else:
                next_task = selected_tasks[task_idx + 1]["question"]
                task_num = task_idx + 2
                emoji_map = {"addition": "🌅", "subtraction": "🌑", "multiplication": "🌳", "division": "🌊", "time_world": "🕒", "measure_world": "📏", "logic_world": "🧠"}
                emoji = emoji_map.get(current_level, "❓")
                task_text = (f"{emoji} *ЗАДАЧА {task_num} из {len(selected_tasks)}*\n{'━' * 10}\n❓ *{next_task}*\n{'━' * 10}")
                await update.message.reply_text(task_text, parse_mode="Markdown", reply_markup=get_game_keyboard())
        else:
            modifiers = calculate_modifiers(user_id, storage)
            penalty = 15
            
            refund_ratio = modifiers.get('penalty_refund_ratio', 0.0)
            if refund_ratio > 0:
                penalty = int(penalty * (1 - refund_ratio))
                await update.message.reply_text(f"🗡️ *КИНЖАЛ РАЗНОСТИ:* Штраф уменьшен на {int(refund_ratio * 100)}%!", parse_mode="Markdown")
                await asyncio.sleep(0.5)
            
            if modifiers.get('mistake_penalty_ignored', False):
                penalty = 0
                await update.message.reply_text("🎩 *ВОЛШЕБНАЯ ШЛЯПА:* Ошибка не штрафуется!", parse_mode="Markdown")
                await asyncio.sleep(0.5)
            elif modifiers.get('ignore_first_mistake', False) and progress.get("mistakes_in_level", 0) == 0:
                penalty = 0
                await update.message.reply_text("🛡️ *ЩИТ ВЫЧИТАНИЯ:* Первая ошибка прощена!", parse_mode="Markdown")
                await asyncio.sleep(0.5)
            
            if penalty > 0:
                if score_manager:
                    score_manager.spend_score(
                        user_id=user_id,
                        amount=penalty,
                        reason="level_task_wrong",
                        context=f"level_{current_level}_task_{task_idx}"
                    )
                    # ✅ ОБНОВЛЯЕМ progress после списания
                    progress["score_balance"] = max(0, progress.get("score_balance", 0) - penalty)
                else:
                    progress["score_balance"] = max(0, progress.get("score_balance", 0) - penalty)
                    storage.save_user(user_id, progress)
                progress["xp"] = max(0, progress.get("xp", 0) - 5)
            
            progress["mistakes_in_level"] = progress.get("mistakes_in_level", 0) + 1
            storage.save_user(user_id, progress)
            
            await send_character_message(update, "manunya", random.choice(["💬 *«Попробуй ещё раз — у тебя получится!»*", "💬 *«Дыши глубже... Ты близка к правильному ответу!»*", "💬 *«Я верю в тебя! Давай ещё разок?»*", "💬 *«Ошибки — это ступеньки к победе!»*"]))
            await asyncio.sleep(0.9)
            await send_character_message(update, "georgy", random.choice(["💚 *«Эй, не парься! Даже я иногда путаю цифры!»*", "💚 *«Ха! Это же просто — попробуй ещё раз!»*", "💚 *«Ошибся? Значит, ты учишься! Так держать!»*"]))
            await asyncio.sleep(0.7)
            
            current_task = selected_tasks[task_idx]["question"]
            emoji_map = {"addition": "🌅", "subtraction": "🌑", "multiplication": "🌳", "division": "🌊", "time_world": "🕒", "measure_world": "📏", "logic_world": "🧠"}
            emoji = emoji_map.get(current_level, "❓")
            task_text = (f"{emoji} *ЗАДАЧА {task_idx + 1} из {len(selected_tasks)}*\n{'━' * 10}\n❓ *{current_task}*\n{'━' * 10}")
            await update.message.reply_text(task_text, parse_mode="Markdown", reply_markup=get_game_keyboard())
        return True
    except ValueError:
        await update.message.reply_text(
            "🔢 Нужно ввести число! Или нажми *Назад* для выхода.",
            parse_mode="Markdown",
            reply_markup=get_game_keyboard()
        )
        return True


async def _complete_level(update, context, progress, user_id, current_level, storage, score_manager=None):
    from handlers.bosses import start_boss_battle, unlock_new_zones
    
    reward_map = {"addition": "звезда_сложения", "subtraction": "амулет_вычитания", "multiplication": "мантия_умножения", "division": "щит_деления"}
    boss_map = {"addition": "null_void", "subtraction": "minus_shadow", "multiplication": "evil_multiplier", "division": "fracosaur", "time_world": "time_keeper", "measure_world": "measure_keeper", "logic_world": "logic_keeper"}
    
    reward = reward_map.get(current_level)
    if reward:
        progress["rewards"] = progress.get("rewards", [])
        progress["rewards"].append(reward)
        await update.message.reply_text(f"🏆 *Уровень пройден!* Ты получаешь: 🥕 *{reward.replace('_', ' ').title()}*", parse_mode="Markdown")
        await asyncio.sleep(0.8)
    
    modifiers = calculate_modifiers(user_id, storage)
    completion_score = 100 * modifiers.get('point_multiplier', 1.0)
    completion_xp = 50 * modifiers.get('xp_multiplier', 1.0)
    
    if modifiers.get('perfect_run_bonus', 0) > 0 and progress.get("mistakes_in_level", 0) == 0:
        completion_score += modifiers.get('perfect_run_bonus', 0)
        await update.message.reply_text(f"💎 *ДРЕВНИЙ АМУЛЕТ:* Без ошибок! +{modifiers.get('perfect_run_bonus', 0)} очков!", parse_mode="Markdown")
        await asyncio.sleep(0.5)
    
    # ✅ НАЧИСЛЕНИЕ ЧЕРЕЗ SCORE_MANAGER + СИНХРОНИЗАЦИЯ progress
    if score_manager:
        score_manager.add_score(
            user_id=user_id,
            amount=int(completion_score),
            reason="level_complete",
            context=f"level_{current_level}"
        )
        # ✅ ОБНОВЛЯЕМ progress с новыми значениями
        progress["total_score"] = progress.get("total_score", 0) + int(completion_score)
        progress["score_balance"] = progress.get("score_balance", 0) + int(completion_score)
    
    progress["xp"] = progress.get("xp", 0) + int(completion_xp)
    
    current_xp = progress["xp"]
    current_level_num = progress.get("level", 1)
    xp_to_next = progress.get("xp_to_next", 50)
    while current_xp >= xp_to_next:
        current_xp -= xp_to_next
        current_level_num += 1
        xp_to_next = 50 + (current_level_num - 1) * 10
        await update.message.reply_text(f"🎉 *ПОЗДРАВЛЯЕМ!* Ты достигла уровня {current_level_num}!", parse_mode="Markdown")
    progress.update({"xp": current_xp, "level": current_level_num, "xp_to_next": xp_to_next})
    
    completed_zones = set(progress.get("completed_zones", []))
    completed_zones.add(current_level)
    progress["completed_zones"] = list(completed_zones)
    storage.save_user(user_id, progress)
    
    boss_id = boss_map.get(current_level)
    defeated_bosses = set(progress.get("defeated_bosses", []))
    
    if boss_id and boss_id not in defeated_bosses:
        boss_names = {"null_void": "Нуль-Пустота", "minus_shadow": "Минус-Тень", "evil_multiplier": "Злой Умножитель", "fracosaur": "Дробозавр", "time_keeper": "Хранитель Времени", "measure_keeper": "Хранитель Мер", "logic_keeper": "Хранитель Логики"}
        boss_name = boss_names.get(boss_id, boss_id.replace('_', ' ').title())
        await update.message.reply_text(f"⚔️ *Внимание!* На горизонте появляется {boss_name}!", parse_mode="Markdown")
        await asyncio.sleep(1.0)
        progress["just_completed_level"] = current_level
        storage.save_user(user_id, progress)
        await start_boss_battle(update, context, boss_id)
    else:
        progress["current_level"] = None
        progress["selected_tasks"] = []
        progress["current_task_index"] = 0
        
        unlock_map = {"addition": "subtraction", "subtraction": "multiplication", "multiplication": "division"}
        next_zone = unlock_map.get(current_level)
        if next_zone:
            unlocked = progress.get("unlocked_zones", ["addition"])
            if next_zone not in unlocked:
                unlocked.append(next_zone)
                progress["unlocked_zones"] = unlocked
                zone_names_ru = {"addition": "Сложение", "subtraction": "Вычитание", "multiplication": "Умножение", "division": "Деление", "time_world": "Хронопия", "measure_world": "Мир Мер", "logic_world": "Мир Логики"}
                zone_name_ru = zone_names_ru.get(next_zone, next_zone.replace('_', ' ').title())
                await update.message.reply_text(f"🔓 *Открыт новый остров:* {zone_name_ru}!", parse_mode="Markdown")
                await asyncio.sleep(0.8)
        
        progress = update_explorer_achievement(progress, current_level)
        storage.save_user(user_id, progress)
        await update.message.reply_text("🎮 Выбери следующее приключение:", reply_markup=get_persistent_keyboard(progress))


def update_explorer_achievement(progress, level_completed):
    if "achievements" not in progress or not isinstance(progress["achievements"], dict):
        progress["achievements"] = {}
    if "explorer" not in progress["achievements"] or not isinstance(progress["achievements"]["explorer"], dict):
        progress["achievements"]["explorer"] = {"level": 0, "current": 0, "target": 2}
    if "accuracy" not in progress["achievements"] or not isinstance(progress["achievements"]["accuracy"], dict):
        progress["achievements"]["accuracy"] = {"level": 0, "current": 0, "target": 5}
    
    valid_zones = ["addition", "subtraction", "multiplication", "division", "secret_level", "final_boss", "time_world", "measure_world", "logic_world", "true_lord"]
    if level_completed in valid_zones:
        ach = progress["achievements"]["explorer"]
        completed_zones = set(progress.get("completed_zones", []))
        completed_zones.add(level_completed)
        progress["completed_zones"] = list(completed_zones)
        ach["current"] = len(completed_zones)
        targets = [2, 4, 6, 7]
        level = 0
        for i, target in enumerate(targets):
            if ach["current"] >= target:
                level = i + 1
        ach["level"] = level
        ach["target"] = targets[min(level, len(targets)-1)] if level < len(targets) else targets[-1]
    return progress