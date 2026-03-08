# handlers/true_lord_battle.py
"""
Эпический бой с Истинным Владыкой Числяндии.
Версия: SQLite + PlayerStorage + Avatar Cache 🗄️🖼️⚔️
"""

import random
import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from config import TASKS_FILE, BOSSES_INFO_FILE
from handlers.utils import load_json, send_character_message
# ✅ УДАЛЕНО: import storage (теперь берём из context.bot_data)
# --- ИМПОРТ НОВОГО МОДУЛЯ ---
from handlers.effects_manager import calculate_modifiers, apply_consumable_effect
from items import SHOP_ITEMS
# -----------------------------
from core.avatar_cache import get_avatar_cache

# === ЗАГРУЗКА ДАННЫХ ===
TASKS_DATA = load_json(TASKS_FILE)
BOSSES_INFO_DATA = load_json(BOSSES_INFO_FILE)


class TrueLordBoss:
    def __init__(self):
        if "bosses" not in TASKS_DATA or "true_lord" not in TASKS_DATA["bosses"]:
            raise KeyError("Ключ 'bosses' или 'true_lord' не найден в TASKS_DATA")
        
        self.tasks = TASKS_DATA["bosses"]["true_lord"]["tasks"]
        required_count = 60
        if len(self.tasks) < required_count:
            multiplier = (required_count // len(self.tasks)) + 1
            extended_tasks = self.tasks * multiplier
            self.tasks = extended_tasks[:required_count]

        self.max_health = 20
        self.current_health = self.max_health
        self.phases = {
            "calm": {"min_hp_percent": 70, "name": "Надменный"},
            "angry": {"min_hp_percent": 30, "name": "Встревоженный"},
            "desperate": {"min_hp_percent": 0, "name": "В панике"}
        }
        self.current_phase = "calm"
        self.error_count = 0
        self.consecutive_successes = 0
        self.last_messages = {
            "calm": [
                "Ошибка невозможна. Всё уже решено.",
                "Ваши попытки… не влияют на результат.",
                "В Числяндии существует только один правильный ответ.",
                "Я — порядок. А порядок не проигрывает.",
                "Вы ещё не поняли правила. А я их создал."
            ],
            "angry": [
                "Это… не соответствует расчётам.",
                "Подожди… так не должно быть.",
                "Повтори вычисление. Результат неверен.",
                "Порядок колеблется… но он устоит.",
                "Нет. Это просто погрешность."
            ],
            "desperate": [
                "Стой! Это нарушает систему!",
                "Такого ответа не существует!",
                "Я… я всё просчитал!",
                "НЕТ! Порядок не может ошибаться!",
                "Остановитесь! Я ещё могу всё исправить!"
            ]
        }
        self.phase_messages = {
            "angry": "Это… не соответствует расчётам. Подожди… так не должно быть.",
            "desperate": "НЕТ! Порядок не может ошибаться! Это невозможно… невозможно…"
        }

    def get_phase(self, current_hp, max_hp):
        percent = (current_hp / max_hp) * 100
        if percent <= self.phases["desperate"]["min_hp_percent"]:
            return "desperate"
        elif percent <= self.phases["angry"]["min_hp_percent"]:
            return "angry"
        else:
            return "calm"

    def select_random_tasks(self, count):
        return random.sample(self.tasks, min(count, len(self.tasks)))

    def apply_psychological_attack(self, update, context, progress, user_was_correct):
        current_hp = progress.get("boss_health", self.max_health)
        max_hp = progress.get("boss_max_health", self.max_health)
        new_phase = self.get_phase(current_hp, max_hp)

        if new_phase != self.current_phase:
            self.current_phase = new_phase
            phase_msg = self.phase_messages.get(new_phase, f"Фаза {new_phase} активирована.")
            asyncio.create_task(send_character_message(update, "true_lord", f"*«{phase_msg}»*"))
            support_messages = {
                "angry": "💬 **Манюня**: *«Он злится! Это значит, ты на правильном пути!»*",
                "desperate": "💬 **Манюня**: *«Морковка, не слушай его! Это *всё* обман!»*"
            }
            support_msg = support_messages.get(new_phase, "*«Держись!»*")
            asyncio.create_task(send_character_message(update, "manunya", support_msg))
            
            avatar_key = f"true_lord_{new_phase}"
            avatar_filename = f"{avatar_key}.jpg"
            avatar_path = os.path.join("images", avatar_filename)

            if os.path.exists(avatar_path):
                async def send_avatar():
                    try:
                        cache = get_avatar_cache()
                        file_id = cache.get_avatar(avatar_key) if cache else None
                        if file_id:
                            await update.message.reply_photo(photo=file_id)
                        else:
                            with open(avatar_path, 'rb') as photo_file:
                                await update.message.reply_photo(photo=photo_file)
                        await asyncio.sleep(0.6)
                    except Exception as e:
                        print(f"[DEBUG] Could not send avatar for {new_phase} phase: {e}")
                        pass
                asyncio.create_task(send_avatar())
            else:
                print(f"[DEBUG] Avatar file for {new_phase} phase not found: {avatar_filename}")

        if not user_was_correct:
            self.error_count += 1
            self.consecutive_successes = 0
            message_pool = self.last_messages[self.current_phase]
            message = random.choice(message_pool)
            message = message.format(count=self.error_count)
            asyncio.create_task(send_character_message(update, "true_lord", f"*«{message}»*"))

            current_task = progress.get("selected_boss_tasks", [])[progress.get("boss_task_index", 0)]
            task_question = current_task.get("question", "").lower()
            task_answer = current_task.get("answer", 0)
            if isinstance(task_answer, str):
                try:
                    task_answer = float(task_answer)
                except ValueError:
                    task_answer = 0

            error_type = "general"
            if "слож" in task_question or "+" in task_question:
                error_type = "addition"
            elif "вычит" in task_question or "-" in task_question:
                error_type = "subtraction"
            elif "умнож" in task_question or "*" in task_question or "×" in task_question:
                error_type = "multiplication"
            elif "делен" in task_question or "/" in task_question or "÷" in task_question:
                error_type = "division"

            georgy_jokes = {
                "addition": [
                    "Так… числа сложились, но как моя слизь в рюкзаке — не совсем аккуратно.",
                    "Ой, тут плюсик вроде был, а стал минусом. У меня так же, когда путаю завтрак и ужин.",
                    "Сложили мы всё правильно… почти. Как носки после стирки — один лишний."
                ],
                "subtraction": [
                    "Мы тут вычли так, что я аж похудел. А я этого не просил!",
                    "Минус — штука коварная. У меня от него слизь иногда убегает.",
                    "Кажется, мы вычли больше, чем нужно. Это как откусить сразу половину бутерброда."
                ],
                "multiplication": [
                    "Ого! Тут чисел стало больше, чем моих следов после дождя.",
                    "Умножение — это когда всё растёт. А тут что-то выросло криво… как я без зарядки.",
                    "Мне нравится этот ответ. Но правильному он не родственник."
                ],
                "division": [
                    "Поделили так, что всем не хватило. Я такое видел на дне рождения без торта.",
                    "Деление любит аккуратность. А тут получилось… по-слизневски.",
                    "Так делить нельзя. Проверено моей слизью — она потом обижается."
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
                    "Ошибки иногда возвращаются. Как я после прогулки."
                ]
            }

            chosen_georgy_joke = random.choice(georgy_jokes.get(error_type, georgy_jokes["general"]))
            manunya_support = "*«Всё в порядке! Просто подумай ещё!»*"
            asyncio.create_task(send_character_message(update, "manunya", manunya_support))
            asyncio.create_task(send_character_message(update, "georgy", f"*«{chosen_georgy_joke}»*"))

        else:
            self.consecutive_successes += 1
            self.error_count = 0
            if self.consecutive_successes >= 5:
                success_messages = {
                    "calm": "Ты... угадала? Везение.",
                    "angry": "Это... невозможно!",
                    "desperate": "Ты... не должна быть... такой сильной...!"
                }
                message = success_messages.get(self.current_phase, "...")
                asyncio.create_task(send_character_message(update, "true_lord", f"*«{message}»*"))

                encouragement_messages = {
                    "calm": "💬 **Манюня**: *«Вот это да! Ты просто огонь!»*",
                    "angry": "💬 **Манюня**: *«Он уже злится! Продолжай в том же духе!»*",
                    "desperate": "💬 **Манюня**: *«Ты почти победила! Не сбавляй обороты!»*"
                }
                chosen_encouragement = random.choice(list(encouragement_messages.values()))
                asyncio.create_task(send_character_message(update, "manunya", chosen_encouragement.split(": ")[1].strip("*").strip('"')))
                
                georgy_success_jokes = [
                    "Вот! Теперь красиво. Прямо как моя слизь после дождя.",
                    "Я горжусь. И слизь тоже.",
                    "Запомни этот момент. Он вкусный. Почти как салат.",
                    "Между прочим… ты думаешь лучше, чем я. А это уже серьёзно."
                ]
                chosen_georgy_success_joke = random.choice(georgy_success_jokes)
                asyncio.create_task(send_character_message(update, "georgy", f"*«{chosen_georgy_success_joke}»*"))


async def start_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск эпического боя с Истинным Владыкой"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    # ✅ ПОЛУЧАЕМ STORAGE ИЗ CONTEXT
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    # ✅ ЧИТАЕМ/СОЗДАЁМ ПОЛЬЗОВАТЕЛЯ
    progress = storage.get_or_create_user(user_id, update.effective_user.username if update.effective_user else None)

    boss_instance = TrueLordBoss()
    selected_tasks = boss_instance.select_random_tasks(60)

    progress.update({
        "in_final_boss": False,
        "in_boss_battle": True,
        "current_boss": "true_lord",
        "selected_boss_tasks": selected_tasks,
        "boss_task_index": 0,
        "boss_health": boss_instance.max_health,
        "boss_max_health": boss_instance.max_health,
        "boss_turn": 0,
        "true_lord_error_count": 0,
        "true_lord_consecutive_successes": 0,
        "true_lord_used_hint": False,
        "true_lord_self_corrections": 0,
        "true_lord_secret_unlocked": progress.get("true_lord_secret_unlocked", False)
    })
    # ✅ СОХРАНЯЕМ ЧЕРЕЗ PlayerStorage
    storage.save_user(user_id, progress)

    await send_character_message(update, "true_lord", "👑👑 **ИСТИННЫЙ ВЛАДЫКА ЧИСЛЯНДИИ**")
    await asyncio.sleep(0.6)

    initial_phase = boss_instance.current_phase
    avatar_key = f"true_lord_{initial_phase}"
    avatar_filename = f"{avatar_key}.jpg"
    avatar_path = os.path.join("images", avatar_filename)

    if os.path.exists(avatar_path):
        try:
            cache = get_avatar_cache()
            file_id = cache.get_avatar(avatar_key) if cache else None
            if file_id:
                await update.message.reply_photo(photo=file_id)
            else:
                with open(avatar_path, 'rb') as photo_file:
                    await update.message.reply_photo(photo=photo_file)
            await asyncio.sleep(0.6)
        except Exception as e:
            print(f"[DEBUG] Could not send initial avatar for {initial_phase} phase: {e}")
            pass
    else:
        print(f"[DEBUG] Initial avatar file for {initial_phase} phase not found: {avatar_filename}")

    await send_character_message(update, "true_lord", f"*«{TASKS_DATA['bosses']['true_lord']['intro']}»*")
    await asyncio.sleep(0.8)
    await send_character_message(update, "manunya", "💬 **Манюня**: *«Будь осторожна, Морковка!»*")
    await asyncio.sleep(0.5)
    await send_character_message(update, "georgy", "💚 **Слизень Георгий**: *«Это он! Главный злодей!»*")
    await asyncio.sleep(0.5)

    first_task = selected_tasks[0]["question"]
    await update.message.reply_text(
        f"⚔️ **БИТВА НАЧАЛАСЬ!**\n\n❓ *{first_task}*\n\n💡 Напиши *подсказка* или *назад* чтобы выйти",
        parse_mode="Markdown"
    )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа в бою с Истинным Владыкой"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    # ✅ ПОЛУЧАЕМ STORAGE ИЗ CONTEXT
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище не инициализировано.")
        return False
    
    # ✅ ЧИТАЕМ ПОЛЬЗОВАТЕЛЯ
    progress = storage.get_user(user_id)
    if not progress:
        return False
    
    selected_tasks = progress.get("selected_boss_tasks", [])
    task_idx = progress.get("boss_task_index", 0)
    boss_health = progress.get("boss_health", 20)
    boss_max_health = progress.get("boss_max_health", 20)
    boss_turn = progress.get("boss_turn", 0)

    if task_idx >= len(selected_tasks) or boss_health <= 0:
        return False

    text = update.message.text.strip()
    user_text = text.lower()

    modifiers = calculate_modifiers(user_id)

    if user_text == "подсказка":
        hint = selected_tasks[task_idx]["hint"]
        await update.message.reply_text(f"💡 *{hint}*", parse_mode="Markdown")
        if not modifiers.get('hint_is_free', False):
            penalty = 10
        else:
            penalty = 0
        if penalty > 0:
            progress["current_score"] = max(0, progress.get("current_score", 0) - penalty)
            progress["xp"] = max(0, progress.get("xp", 0) - 5)
        progress["true_lord_used_hint"] = True
        storage.save_user(user_id, progress)
        return True

    try:
        answer = int(float(text))
        task = selected_tasks[task_idx]

        boss_instance = TrueLordBoss()
        boss_instance.max_health = boss_max_health
        boss_instance.current_health = boss_health
        boss_instance.error_count = progress.get("true_lord_error_count", 0)
        boss_instance.consecutive_successes = progress.get("true_lord_consecutive_successes", 0)

        user_was_correct = (answer == task["answer"])

        if user_was_correct:
            correct_answers = task_idx + 1
            progress["boss_task_index"] = correct_answers
            
            base_score = 150
            base_xp = 20
            
            point_multiplier = modifiers.get('point_multiplier', 1.0)
            next_task_multiplier = modifiers.get('next_task_point_multiplier', 1.0)
            total_point_multiplier = point_multiplier * next_task_multiplier
            
            earned_score = base_score * total_point_multiplier
            
            xp_bonus = modifiers.get('xp_bonus_per_task', 0)
            xp_multiplier = modifiers.get('xp_multiplier', 1.0)
            earned_xp = (base_xp + xp_bonus) * xp_multiplier
            
            instant_bonus_applied = modifiers.get('instant_score_gain', 0)
            
            progress["current_score"] = progress.get("current_score", 0) + earned_score + instant_bonus_applied
            
            current_xp = progress.get("xp", 0)
            xp_to_next = progress.get("xp_to_next", 50)
            current_level_num = progress.get("level", 1)

            current_xp += earned_xp

            while current_xp >= xp_to_next:
                current_xp -= xp_to_next
                current_level_num += 1
                xp_to_next = 50 + (current_level_num - 1) * 10
                await update.message.reply_text(
                    f"🎉 *ПОЗДРАВЛЯЕМ!* Ты достигла уровня {current_level_num}!",
                    parse_mode="Markdown"
                )

            progress["xp"] = current_xp
            progress["level"] = current_level_num
            progress["xp_to_next"] = xp_to_next
            
            boss_instance.current_health -= 1

            if boss_instance.current_health <= 0:
                base_victory_score_bonus = 500
                victory_score_multiplier = modifiers.get('point_multiplier', 1.0)
                earned_victory_score_bonus = base_victory_score_bonus * victory_score_multiplier
                
                progress["current_score"] = progress.get("current_score", 0) + earned_victory_score_bonus
                
                base_victory_xp_bonus = 200
                victory_xp_bonus = modifiers.get('xp_bonus_per_task', 0)
                victory_xp_multiplier = modifiers.get('xp_multiplier', 1.0)
                earned_victory_xp_bonus = (base_victory_xp_bonus + victory_xp_bonus) * victory_xp_multiplier

                current_xp = progress.get("xp", 0)
                xp_to_next = progress.get("xp_to_next", 50)
                current_level_num = progress.get("level", 1)

                current_xp += earned_victory_xp_bonus

                while current_xp >= xp_to_next:
                    current_xp -= xp_to_next
                    current_level_num += 1
                    xp_to_next = 50 + (current_level_num - 1) * 10
                    await update.message.reply_text(
                        f"🎉 *ПОЗДРАВЛЯЕМ!* Ты достигла уровня {current_level_num}!",
                        parse_mode="Markdown"
                    )

                progress["xp"] = current_xp
                progress["level"] = current_level_num
                progress["xp_to_next"] = xp_to_next
                
                reward = TASKS_DATA["bosses"]["true_lord"]["reward"]
                progress["rewards"] = progress.get("rewards", [])
                progress["rewards"].append(reward)

                final_score = progress.get("current_score", 0)
                best_score = progress.get("best_score", 0)
                total_games = progress.get("total_games", 0) + 1

                if final_score > best_score:
                    progress["best_score"] = final_score
                    victory_msg = f"🎉 *НОВЫЙ РЕКОРД!* Твой счёт: {final_score}!"
                else:
                    victory_msg = f"✨ Отлично! Твой счёт: {final_score}\nЛучший рекорд: {best_score}"

                progress["completed_normal_game"] = True
                progress["absolute_victory"] = True

                progress.update({
                    "in_final_boss": False,
                    "in_boss_battle": False,
                    "current_boss": None,
                    "selected_boss_tasks": [],
                    "boss_task_index": 0,
                    "boss_health": 0,
                    "boss_max_health": 0,
                    "boss_turn": 0,
                    "total_games": total_games
                })
                storage.save_user(user_id, progress)

                await send_character_message(update, "true_lord", f"*«{TASKS_DATA['bosses']['true_lord']['victory']}»*")
                
                used_hint = progress.get("true_lord_used_hint", False)
                should_show_secret = not used_hint and not progress.get("true_lord_secret_unlocked", False)

                if should_show_secret:
                    secret_text = (
                        "🔒 СЕКРЕТНАЯ РЕПЛИКА\n"
                        "Истинный Владыка (тихо):\n"
                        "«Ты заметила то, что не все видят…\n"
                        "Ошибка — это не поражение.\n"
                        "Это путь к пониманию.»\n"
                        "«Если бы я понял это раньше,\n"
                        "Числяндия не нуждалась бы в спасении.»\n\n"
                        "💛 Манюня (шёпотом):\n"
                        "«Это секрет.\n"
                        "Его слышат только те, кто действительно думает.»\n\n"
                        "🐌 Георгий:\n"
                        "«И знаешь что?\n"
                        "Теперь он — твой.»"
                    )
                    await update.message.reply_text(secret_text, parse_mode="Markdown")
                    progress["true_lord_secret_unlocked"] = True
                    storage.save_user(user_id, progress)

                finale_text = (
                    "🌟 ФИНАЛЬНЫЙ ЭКРАН · ПОБЕДА В ЧИСЛЯНДИИ\n"
                    "✨ ПОРЯДОК РУШИТСЯ…\n"
                    "И ЧИСЛЯНДИЯ ПРОСЫПАЕТСЯ ✨\n\n"
                    "Истинный Владыка исчезает,\n"
                    "а цифры больше не боятся ошибок.\n\n"
                    "Числяндия снова живая.\n"
                    "Здесь можно думать.\n"
                    "Пробовать.\n"
                    "И находить свой путь к ответу.\n\n"
                    "Ты победила не силой —\n"
                    "а умением рассуждать.\n"
                    "Не потому что всё знала,\n"
                    "а потому что не сдавалась.\n\n"
                    "💛 Манюня улыбается:\n"
                    "«Видишь? Математика — это не страх.\n"
                    "Это игра, где ты умеешь думать.»\n\n"
                    "🐌 Георгий важно кивает:\n"
                    "«Даже если ошиблась —\n"
                    "это просто шаг к правильному ответу.»\n\n"
                    "🏆 ПОЗДРАВЛЯЕМ!\n"
                    "Ты освободила Числяндию\n"
                    "и доказала, что:\n"
                    "✨ самое сильное число — это уверенность в себе ✨\n\n"
                    "🔔 КНОПКА / ПРОДОЛЖЕНИЕ\n"
                    "[ Продолжить приключения ]\n"
                    "[ Сыграть ещё раз ]"
                )
                
                await update.message.reply_text(finale_text, parse_mode="Markdown")
                
                await send_character_message(update, "manunya", "💬 **Манюня**: *«Морковка, ты — ЛЕГЕНДА ЧИСЛЯНДИИ!»*")
                await send_character_message(update, "georgy", "💚 **Слизень Георгий**: *«Ха-ха! Я знал, что ты справишься!»*")
                
                await update.message.reply_text(
                    f"{victory_msg}\n\nТы получаешь: 🥕 *{reward.replace('_', ' ').title()}*!\n\n"
                    "🌟 **АБСОЛЮТНАЯ ПОБЕДА!**",
                    parse_mode="Markdown"
                )
            else:
                progress["boss_health"] = boss_instance.current_health
                progress["boss_turn"] = boss_turn + 1
                progress["true_lord_error_count"] = boss_instance.error_count
                progress["true_lord_consecutive_successes"] = boss_instance.consecutive_successes

                storage.save_user(user_id, progress)
                
                if instant_bonus_applied > 0:
                    inventory = progress.get("inventory", [])
                    item_to_remove = None
                    for item_id in inventory:
                        item_data = SHOP_ITEMS.get(item_id)
                        if item_data and item_data.get("effect") == "gain_x_points" and item_data.get("type") == "consumable_single_use":
                            item_to_remove = item_id
                            break
                    
                    if item_to_remove:
                        inventory.remove(item_to_remove)
                        progress["inventory"] = inventory
                        item_name = SHOP_ITEMS[item_to_remove]['name']
                        await update.message.reply_text(
                            f"✨ *Активация!* Использовано: **{item_name}**! Ты получаешь **+{instant_bonus_applied}** очков!",
                            parse_mode="Markdown"
                        )

                next_q = selected_tasks[correct_answers]["question"]
                health_bar = "❤️" * boss_instance.current_health + "💔" * (boss_instance.max_health - boss_instance.current_health)
                await update.message.reply_text(
                    f"✅ Отлично! Здоровье Владыки: {health_bar}\n\n❓ *{next_q}*",
                    parse_mode="Markdown"
                )
                boss_instance.apply_psychological_attack(update, context, progress, True)
                await send_character_message(update, "manunya", "*«Держись, Морковка! Ты крутая!»*")
                await send_character_message(update, "georgy", "*«Так держать! Он *всё* ревёт!»*")
        else:
            if not modifiers.get('mistake_penalty_ignored', False):
                penalty = 20
            else:
                penalty = 0
            
            if penalty > 0:
                current_score = progress.get("current_score", 0)
                current_score = max(0, current_score - penalty)
                progress["current_score"] = current_score
            
            current_xp = progress.get("xp", 0)
            current_xp = max(0, current_xp - 10)
            progress["xp"] = current_xp
            
            progress["boss_turn"] = boss_turn + 1
            boss_instance.error_count = progress.get("true_lord_error_count", 0) + 1
            boss_instance.consecutive_successes = 0
            progress["true_lord_error_count"] = boss_instance.error_count
            progress["true_lord_consecutive_successes"] = boss_instance.consecutive_successes

            storage.save_user(user_id, progress)
            boss_instance.apply_psychological_attack(update, context, progress, False)
            
        return True
    except ValueError:
        await update.message.reply_text("Нужно число! Владыка ждёт твой удар! ⚔️")
        return True