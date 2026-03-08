import random
import os
from telegram import Update
from telegram.ext import ContextTypes
from config import PROGRESS_FILE, BOSS_DATA_DIR
from handlers.utils import load_json, save_json, send_character_message

# === ЗАГРУЗКА ДАННЫХ ===
BOSS_DATA = load_json(os.path.join(BOSS_DATA_DIR, "final_boss.json"))

class FinalBoss:
    def __init__(self):
        self.max_health = 8  # Увеличенное HP для финального босса
        self.current_health = 8
        self.abilities = {
            "math_absorption": {"name": "Поглощение Математики", "chance": 0.6},      # При ошибке
            "chaos_multiplication": {"name": "Хаотическое Умножение", "chance": 0.4},   # Каждый ход
            "time_reversal": {"name": "Обратное Время", "chance": 0.3},                # При HP ≤ 3
            "ultimate_divide": {"name": "Ультимативное Деление", "chance": 0.5}        # При HP ≤ 2
        }
    
    async def use_math_absorption(self, update, context, progress):
        """Поглощение Математики: крадёт 15 очков и восстанавливает 2 HP при ошибке"""
        if random.random() < self.abilities["math_absorption"]["chance"]:
            current_score = progress.get("current_score", 0)
            stolen = min(15, current_score)
            progress["current_score"] = max(0, current_score - stolen)
            
            # Восстанавливает 2 HP за каждые 10 украденных очков
            hp_gain = (stolen // 10) * 2
            if hp_gain > 0:
                self.current_health = min(self.max_health, self.current_health + hp_gain)
                progress["boss_health"] = self.current_health
                await update.message.reply_text(f"👑 *Владыка поглотил {stolen} твоих очков и восстановил {hp_gain} жизни!*")
            else:
                await update.message.reply_text(f"👑 *Владыка поглотил {stolen} твоих очков!*")
            save_json(PROGRESS_FILE, progress)
            return True
        return False
    
    async def use_chaos_multiplication(self, update, context, progress):
        """Хаотическое Умножение: удваивает количество оставшихся задач с шансом 40%"""
        if random.random() < self.abilities["chaos_multiplication"]["chance"]:
            selected_tasks = progress.get("selected_boss_tasks", [])
            task_idx = progress.get("boss_task_index", 0)
            remaining_tasks = selected_tasks[task_idx:]
            
            if len(remaining_tasks) < 8:  # Ограничение, чтобы не было слишком много задач
                # Дублируем оставшиеся задачи
                new_tasks = remaining_tasks + remaining_tasks
                selected_tasks = selected_tasks[:task_idx] + new_tasks
                progress["selected_boss_tasks"] = selected_tasks
                
                await update.message.reply_text("👑 *Владыка удвоил оставшиеся задачи!*")
                save_json(PROGRESS_FILE, progress)
                return True
        return False
    
    async def use_time_reversal(self, update, context, progress):
        """Обратное Время: возвращает одну решённую задачу обратно (игрок должен решить её снова)"""
        if self.current_health <= 3 and random.random() < self.abilities["time_reversal"]["chance"]:
            task_idx = progress.get("boss_task_index", 0)
            if task_idx > 1:  # Можно вернуть только если решено больше 1 задачи
                # Возвращаем на предыдущую задачу
                progress["boss_task_index"] = task_idx - 1
                selected_tasks = progress.get("selected_boss_tasks", [])
                previous_task = selected_tasks[task_idx - 1]["question"]
                
                await update.message.reply_text(f"⏳ *Владыка повернул время назад! Тебе нужно решить снова:*\n\n{previous_task}")
                save_json(PROGRESS_FILE, progress)
                return True
        return False
    
    async def use_ultimate_divide(self, update, context, progress):
        """Ультимативное Деление: делит текущее здоровье игрока на 2 (если HP > 50)"""
        if self.current_health <= 2 and random.random() < self.abilities["ultimate_divide"]["chance"]:
            current_score = progress.get("current_score", 0)
            if current_score > 50:
                new_score = current_score // 2
                progress["current_score"] = new_score
                await update.message.reply_text(f"⚔️ *Владыка применил УЛЬТИМАТИВНОЕ ДЕЛЕНИЕ! Твои очки разделены пополам: {new_score}*")
                save_json(PROGRESS_FILE, progress)
                return True
        return False

async def start_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск эпического боя с Владыкой Числяндии"""
    progress = load_json(PROGRESS_FILE)
    
    # Выбираем 6 случайных задач из 30 (больше задач для финального босса)
    all_tasks = BOSS_DATA["tasks"]
    selected_tasks = random.sample(all_tasks, min(6, len(all_tasks)))
    
    # Инициализация босса
    boss = FinalBoss()
    
    # Сохраняем состояние
    progress.update({
        "in_final_boss": True,
        "in_boss_battle": False,
        "current_boss": "final_boss",
        "selected_boss_tasks": selected_tasks,
        "boss_task_index": 0,
        "boss_health": boss.current_health,
        "boss_max_health": boss.max_health,
        "boss_turn": 0
    })
    save_json(PROGRESS_FILE, progress)
    
    # Отправляем эпические сообщения
    await send_character_message(update, "manunya", "👑 **ВЛАДЫКА ЧИСЛЯНДИИ**")
    await send_character_message(update, "manunya", f"💬 **Манюня**: {BOSS_DATA['intro']}")
    await send_character_message(update, "georgy", "💚 **Слизень Георгий**: *«Это он! Главный злодей! Не дай ему стереть математику!»*")
    
    first_task = selected_tasks[0]["question"]
    await update.message.reply_text(f"{BOSS_DATA['intro']}\n\n{first_task}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа в эпическом бою с Владыкой"""
    progress = load_json(PROGRESS_FILE)
    selected_tasks = progress.get("selected_boss_tasks", [])
    task_idx = progress.get("boss_task_index", 0)
    boss_health = progress.get("boss_health", 8)
    boss_max_health = progress.get("boss_max_health", 8)
    boss_turn = progress.get("boss_turn", 0)
    
    if task_idx >= len(selected_tasks) or boss_health <= 0:
        return False
    
    text = update.message.text.strip()
    user_text = text.lower()
    
    # Обработка подсказки
    if user_text == "подсказка":
        hint = selected_tasks[task_idx]["hint"]
        await update.message.reply_text(f"💡 {hint}")
        progress["current_score"] = progress.get("current_score", 0) - 5
        save_json(PROGRESS_FILE, progress)
        return True
    
    try:
        answer = int(text)
        task = selected_tasks[task_idx]
        boss = FinalBoss()
        boss.current_health = boss_health
        boss.max_health = boss_max_health
        
        if answer == task["answer"]:
            # === ПРАВИЛЬНЫЙ ОТВЕТ ===
            correct_answers = task_idx + 1
            progress["boss_task_index"] = correct_answers
            progress["current_score"] = progress.get("current_score", 0) + 35  # Больше очков за финального босса
            boss.current_health -= 1  # Урон боссу
            
            if boss.current_health <= 0:
                # === ЭПИЧЕСКАЯ ПОБЕДА ===
                reward = BOSS_DATA["reward"]
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
                
                # Открываем Портал Осколков
                progress["completed_normal_game"] = True
                
                progress.update({
                    "in_final_boss": False,
                    "current_boss": None,
                    "selected_boss_tasks": [],
                    "boss_task_index": 0,
                    "boss_health": 0,
                    "total_games": total_games
                })
                save_json(PROGRESS_FILE, progress)
                
                await send_character_message(update, "manunya", BOSS_DATA["victory"])
                await send_character_message(update, "manunya", "💬 **Манюня**: *«Морковка, ты — легенда Числяндии!»*")
                await send_character_message(update, "georgy", "💚 **Слизень Георгий**: *«Ха! Я знал, что ты справишься!»*")
                await update.message.reply_text(
                    f"{victory_msg}\n\nТы получаешь: 🥕 *{reward.replace('_', ' ').title()}*!\n\n"
                    "🌀 **ПОРТАЛ ОСКОЛКОВ** открыт! Исследуй новые миры!",
                    parse_mode="Markdown"
                )
            else:
                # === ПРОДОЛЖЕНИЕ ЭПИЧЕСКОГО БОЯ ===
                progress["boss_health"] = boss.current_health
                progress["boss_turn"] = boss_turn + 1
                
                # Проверяем способности
                if boss.current_health <= 3:
                    await boss.use_time_reversal(update, context, progress)
                
                if boss.current_health <= 2:
                    await boss.use_ultimate_divide(update, context, progress)
                
                # Хаотическое умножение может сработать каждый ход
                await boss.use_chaos_multiplication(update, context, progress)
                
                save_json(PROGRESS_FILE, progress)
                next_q = selected_tasks[correct_answers]["question"]
                health_bar = "❤️" * boss.current_health + "💔" * (boss.max_health - boss.current_health)
                await update.message.reply_text(f"✅ Отлично! Здоровье Владыки: {health_bar}\n\n{next_q}")
        else:
            # === ОШИБКА ИГРОКА ===
            progress["current_score"] = progress.get("current_score", 0) - 15  # Больший штраф за финального босса
            progress["boss_turn"] = boss_turn + 1
            
            # Владыка использует способность "Поглощение Математики"
            await boss.use_math_absorption(update, context, progress)
            
            save_json(PROGRESS_FILE, progress)
            encourage = "💬 **Манюня**: *«Не сдавайся! Ты почти победила!»*"
            georgy_msg = "🟢 **Слизень Георгий**: *«Ой-ой! Но ты — настоящая Матемаг!»*"
            await update.message.reply_text(f"{encourage}\n\n{georgy_msg}", parse_mode="Markdown")
        return True
    except ValueError:
        await update.message.reply_text("Нужно число! Владыка ждёт твой удар! ⚔️")
        return True