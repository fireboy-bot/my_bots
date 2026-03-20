# handlers/profile.py
"""
Обработчики профиля, достижений и Замка.
Версия: 2.3 (Fix: Candels + Portrait Math Typos) 🗄️🎒💰🔮🕯️🖼️

Изменения:
- ✅ Исправлены иконки артефактов (полное совпадение ID)
- ✅ Показываем ВСЕ предметы (без обрезки после 7)
- ✅ Показываем уровни артефактов в инвентаре
- ✅ ИСПРАВЛЕНЫ ОПЕЧАТКИ: candels → 🕯️, portrait_maty → 🖼️
- ✅ logging вместо print()
- ✅ Экранирование пользовательских данных
"""

import asyncio
import random
import re
import logging
from collections import Counter
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import BASE_DIR
from core.logger import log_user_action

logger = logging.getLogger(__name__)


# === ЭКРАНИРОВАНИЕ ДЛЯ MARKDOWN ===
def escape_markdown(text):
    """Экранирует спецсимволы для простого Markdown"""
    if not text:
        return text
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def get_level_info(total_score: int):
    """Возвращает уровень и звание по очкам"""
    levels = [
        (0, 1, "Ученик"),
        (500, 6, "Исследователь"),
        (2000, 11, "Матемаг"),
        (5000, 16, "Хранитель Чисел"),
        (12000, 21, "Владыка Числяндии")
    ]
    
    for score, level_num, title in reversed(levels):
        if total_score >= score:
            return level_num, title
    
    return 1, "Ученик"


def get_accuracy_info(tasks_correct: int, tasks_solved: int):
    """Возвращает точность и её уровень"""
    if tasks_solved == 0:
        return 0, "🌱 Новичок", "🔴"
    
    accuracy = int((tasks_correct / tasks_solved) * 100)
    
    if accuracy >= 90:
        return accuracy, "🌟 Золотой уровень", "🟢"
    elif accuracy >= 75:
        return accuracy, "🥈 Серебряный уровень", "🟡"
    elif accuracy >= 60:
        return accuracy, "🥉 Бронзовый уровень", "🟠"
    else:
        return accuracy, "🌱 Ученик", "🔴"


def get_item_display(item_id: str):
    """
    Возвращает отображение предмета для инвентаря.
    ✅ ВКЛЮЧАЕТ ВСЕ АРТЕФАКТЫ + ИСПРАВЛЕНИЯ ОПЕЧАТОК (candels, portrait_maty)
    """
    # === 🔮 АРТЕФАКТЫ (ПЕРВЫМИ! для быстрого доступа) ===
    artifact_items = {
        "artifact_luck": {"emoji": "🍀", "name": "Артефакт Удачи", "rarity": "легендарный"},
        "artifact_power": {"emoji": "⚡", "name": "Артефакт Силы", "rarity": "легендарный"},
        "artifact_wisdom": {"emoji": "🧠", "name": "Артефакт Мудрости", "rarity": "легендарный"},
    }
    
    # Проверяем артефакты СНАЧАЛА
    item_lower = item_id.lower()
    if item_lower in artifact_items:
        item = artifact_items[item_lower]
        return f"{item['emoji']} {item['name']} ✨"
    
    # === ВСЕ ОСТАЛЬНЫЕ ПРЕДМЕТЫ (включая варианты с опечатками) ===
    items = {
        # === 🔮 ИСПРАВЛЕНИЯ ОПЕЧАТОК ===
        "candels": {"emoji": "🕯️", "name": "Серебряные подсвечники", "rarity": "обычный"},
        "candles": {"emoji": "🕯️", "name": "Серебряные подсвечники", "rarity": "обычный"},
        "portrait_maty": {"emoji": "🖼️", "name": "Портрет Пифагора", "rarity": "обычный"},
        "portrait_math": {"emoji": "🖼️", "name": "Портрет Пифагора", "rarity": "обычный"},
        
        # === ОСТРОВ СЛОЖЕНИЯ ===
        "sum_gloves": {"emoji": "🧤", "name": "Перчатки Сумматора", "rarity": "обычный"},
        "unity_stone": {"emoji": "💎", "name": "Камень Единства", "rarity": "обычный"},
        
        # === ОСТРОВ ВЫЧИТАНИЯ ===
        "difference_dagger": {"emoji": "🗡️", "name": "Кинжал Разности", "rarity": "обычный"},
        "subtraction_shield": {"emoji": "🛡️", "name": "Щит Вычитания", "rarity": "редкий"},
        "ancient_amulet": {"emoji": "🔮", "name": "Древний Амулет", "rarity": "редкий"},
        
        # === УНИВЕРСАЛЬНЫЕ ПРЕДМЕТЫ ===
        "accuracy_amulet": {"emoji": "📿", "name": "Амулет Точности", "rarity": "редкий"},
        "magic_hat": {"emoji": "🎩", "name": "Волшебная Шляпа", "rarity": "редкий"},
        
        # === СПЕЦИАЛЬНЫЕ ПРЕДМЕТЫ ===
        "math_crown": {"emoji": "👑", "name": "Корона Матемага", "rarity": "легендарный"},
        
        # === АЛХИМИЧЕСКИЕ ПРЕДМЕТЫ ===
        "bravery_potion": {"emoji": "🧪", "name": "Зелье Смелости", "rarity": "редкий"},
        "chaos_cup": {"emoji": "🍷", "name": "Кубок Хаоса", "rarity": "эпический"},
        "dice_of_fate": {"emoji": "🎲", "name": "Кубик Судьбы", "rarity": "эпический"},
        "madness_potion": {"emoji": "💀", "name": "Зелье Безумия", "rarity": "легендарный"},
        
        # === НАГРАДЫ ЗА БОССОВ ===
        "звезда_сложения": {"emoji": "⭐", "name": "Звезда Сложения", "rarity": "обычный"},
        "амулет_вычитания": {"emoji": "🔮", "name": "Амулет Вычитания", "rarity": "обычный"},
        "мантия_умножения": {"emoji": "✨", "name": "Мантия Умножения", "rarity": "редкий"},
        "щит_деления": {"emoji": "🛡️", "name": "Щит Деления", "rarity": "редкий"},
        "корона_матемага": {"emoji": "👑", "name": "Корона Матемага", "rarity": "легендарный"},
        "золотая_морковка": {"emoji": "🥕", "name": "Золотая Морковка", "rarity": "особый"},
        
        # === АНГЛИЙСКИЕ ВЕРСИИ ===
        "star_addition": {"emoji": "⭐", "name": "Звезда Сложения", "rarity": "обычный"},
        "amulet_subtraction": {"emoji": "🔮", "name": "Амулет Вычитания", "rarity": "обычный"},
        "mantle_multiplication": {"emoji": "✨", "name": "Мантия Умножения", "rarity": "редкий"},
        "shield_division": {"emoji": "🛡️", "name": "Щит Деления", "rarity": "редкий"},
        "crown_mathmage": {"emoji": "👑", "name": "Корона Матемага", "rarity": "легендарный"},
        "carrot_golden": {"emoji": "🥕", "name": "Золотая Морковка", "rarity": "особый"},
        "potion_luck": {"emoji": "🧪", "name": "Зелье Удачи", "rarity": "обычный"},
        "ring_power": {"emoji": "💍", "name": "Кольцо Силы", "rarity": "редкий"},
        "gloves_sum": {"emoji": "🧤", "name": "Перчатки Сложения", "rarity": "обычный"},
        "gloves_sub": {"emoji": "🧤", "name": "Перчатки Вычитания", "rarity": "обычный"},
        "gloves_mul": {"emoji": "🧤", "name": "Перчатки Умножения", "rarity": "обычный"},
        "gloves_div": {"emoji": "🧤", "name": "Перчатки Деления", "rarity": "обычный"},
        
        # === ТРОФЕИ ===
        "statue_null": {"emoji": "🗿", "name": "Статуя Нуль-Пустоты", "rarity": "особый"},
        "mirror_shadow": {"emoji": "🪞", "name": "Зеркало Теней", "rarity": "особый"},
        "tree_multiply": {"emoji": "🌳", "name": "Дерево Множеств", "rarity": "особый"},
        "fountain_fracosaur": {"emoji": "🌊", "name": "Фонтан Дробей", "rarity": "особый"},
        "статуя_нуля": {"emoji": "🗿", "name": "Статуя Нуль-Пустоты", "rarity": "особый"},
        "зеркало_теней": {"emoji": "🪞", "name": "Зеркало Теней", "rarity": "особый"},
        "дерево_множеств": {"emoji": "🌳", "name": "Дерево Множеств", "rarity": "особый"},
        "фонтан_дробей": {"emoji": "🌊", "name": "Фонтан Дробей", "rarity": "особый"}
    }
    
    # Пытаемся найти предмет
    item = items.get(item_lower)
    
    if item:
        rarity_emoji = {
            "обычный": "",
            "редкий": "🌟",
            "эпический": "💜",
            "легендарный": "✨",
            "особый": "💫"
        }
        rarity_tag = rarity_emoji.get(item["rarity"], "")
        return f"{item['emoji']} {item['name']} {rarity_tag}".strip()
    
    # === FALLBACK: если предмет не найден ===
    # Обработка артефактов в fallback
    if item_lower.startswith("artifact_"):
        artifact_names = {
            "artifact_luck": "🍀 Артефакт Удачи",
            "artifact_power": "⚡ Артефакт Силы", 
            "artifact_wisdom": "🧠 Артефакт Мудрости"
        }
        name = artifact_names.get(item_lower, item_id.replace("_", " ").title())
        return f"{name} ✨"
    
    # ✅ ПРОВЕРКА НА ПОДОБИЕ (для опечаток)
    if "candel" in item_lower or "candl" in item_lower:
        return f"🕯️ Серебряные подсвечники"
    elif "portrait" in item_lower and "maty" in item_lower:
        return f"🖼️ Портрет Пифагора"
    elif "portrait" in item_lower and "math" in item_lower:
        return f"🖼️ Портрет Пифагора"
    elif "sum" in item_lower or "add" in item_lower or "слож" in item_lower:
        return f"🧤 Перчатки Сложения"
    elif "sub" in item_lower or "minus" in item_lower or "вычит" in item_lower:
        return f"🧤 Перчатки Вычитания"
    elif "mul" in item_lower or "mult" in item_lower or "умнож" in item_lower:
        return f"🧤 Перчатки Умножения"
    elif "div" in item_lower or "дроб" in item_lower or "делен" in item_lower:
        return f"🧤 Перчатки Деления"
    elif "star" in item_lower or "звезда" in item_lower:
        return f"⭐ Звезда Сложения"
    elif "amulet" in item_lower or "амулет" in item_lower:
        return f"🔮 Амулет"
    elif "mantle" in item_lower or "мантия" in item_lower:
        return f"✨ Мантия Умножения"
    elif "shield" in item_lower or "щит" in item_lower:
        return f"🛡️ Щит"
    elif "potion" in item_lower or "зелье" in item_lower:
        return f"🧪 Зелье"
    elif "ring" in item_lower or "кольцо" in item_lower:
        return f"💍 Кольцо"
    elif "crown" in item_lower or "корона" in item_lower:
        return f"👑 Корона"
    elif "carrot" in item_lower or "морков" in item_lower:
        return f"🥕 Золотая Морковка"
    elif "statue" in item_lower or "статуя" in item_lower:
        return f"🗿 Статуя"
    elif "mirror" in item_lower or "зеркало" in item_lower:
        return f"🪞 Зеркало"
    elif "tree" in item_lower or "дерево" in item_lower:
        return f"🌳 Дерево"
    elif "fountain" in item_lower or "фонтан" in item_lower:
        return f"🌊 Фонтан"
    elif "dagger" in item_lower or "кинжал" in item_lower:
        return f"🗡️ Кинжал"
    elif "stone" in item_lower or "камень" in item_lower:
        return f"💎 Камень"
    elif "hat" in item_lower or "шляпа" in item_lower:
        return f"🎩 Волшебная Шляпа"
    elif "chaos" in item_lower or "хаос" in item_lower:
        return f"🍷 Кубок Хаоса"
    elif "dice" in item_lower or "кубик" in item_lower:
        return f"🎲 Кубик Судьбы"
    elif "madness" in item_lower or "безум" in item_lower:
        return f"💀 Зелье Безумия"
    elif "bravery" in item_lower or "смел" in item_lower:
        return f"🧪 Зелье Смелости"
    
    # Совсем неизвестный предмет
    return f"📦 {item_id.replace('_', ' ').title()}"


def get_achievement_display(achievement_id: str, unlocked: bool):
    """Возвращает отображение достижения"""
    achievements = {
        "first_step": {"emoji": "🥚", "name": "Первый шаг", "desc": "Пройти первый остров"},
        "fire_path": {"emoji": "🔥", "name": "Огненный путь", "desc": "5 правильных ответов подряд"},
        "ice_accuracy": {"emoji": "❄️", "name": "Ледяная точность", "desc": "10 правильных ответов подряд"},
        "zero_victory": {"emoji": "💀", "name": "Победитель Смерти", "desc": "Победить Нуль-Пустоту"},
        "shadow_victory": {"emoji": "🌑", "name": "Повелитель Теней", "desc": "Победить Минус-Тень"},
        "multiply_victory": {"emoji": "🌀", "name": "Хозяин Умножения", "desc": "Победить Злого Умножителя"},
        "fracosaur_victory": {"emoji": "🌊", "name": "Укротитель Дробей", "desc": "Победить Дробозавра"},
        "lord_victory": {"emoji": "👑", "name": "Коронация", "desc": "Победить Истинного Владыку"},
        "quick_mind": {"emoji": "⚡", "name": "Быстрый ум", "desc": "Решить 5 задач за 1 минуту"},
        "explorer": {"emoji": "🗺️", "name": "Исследователь", "desc": "Открыть все острова"}
    }
    
    ach = achievements.get(achievement_id, {"emoji": "❓", "name": "Неизвестное достижение", "desc": ""})
    
    if unlocked:
        return f"✅ {ach['emoji']} «{ach['name']}» — {ach['desc']}"
    else:
        return f"🔲 {ach['emoji']} «{ach['name']}» — {ach['desc']}"


def get_trophy_display(trophy_id: str):
    """Возвращает отображение трофея"""
    trophies = {
        "statue_null": {"emoji": "🗿", "name": "Статуя Нуль-Пустоты", "effect": "+5% к очкам за сложение"},
        "mirror_shadow": {"emoji": "🪞", "name": "Зеркало Теней", "effect": "+5% к очкам за вычитание"},
        "tree_multiply": {"emoji": "🌳", "name": "Дерево Множеств", "effect": "+5% к очкам за умножение"},
        "fountain_fracosaur": {"emoji": "🌊", "name": "Фонтан Дробей", "effect": "+5% к очкам за деление"},
        "статуя_нуля": {"emoji": "🗿", "name": "Статуя Нуль-Пустоты", "effect": "+5% к очкам за сложение"},
        "зеркало_теней": {"emoji": "🪞", "name": "Зеркало Теней", "effect": "+5% к очкам за вычитание"},
        "дерево_множеств": {"emoji": "🌳", "name": "Дерево Множеств", "effect": "+5% к очкам за умножение"},
        "фонтан_дробей": {"emoji": "🌊", "name": "Фонтан Дробей", "effect": "+5% к очкам за деление"}
    }
    
    trophy = trophies.get(trophy_id, {"emoji": "🏆", "name": "Неизвестный трофей", "effect": ""})
    return f"{trophy['emoji']} {trophy['name']} — {trophy['effect']}"


# ========================================
# ✅ ФУНКЦИЯ ПРОФИЛЯ (SQLite)
# ========================================
async def show_profile_and_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает основной профиль игрока"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    logger.info(f"🔍 show_profile_and_rewards вызвана для user_id={user_id}")
    
    storage = context.bot_data.get('storage')
    if not storage:
        logger.error("❌ Ошибка: storage не найден в context.bot_data")
        await update.message.reply_text("⚠️ Ошибка: хранилище данных не инициализировано.")
        return
    
    user_data = storage.get_user(user_id)
    
    if not user_data:
        logger.error(f"❌ Ошибка: user_data не найден для user_id={user_id}")
        await update.message.reply_text("❌ Профиль не найден. Попробуйте /start")
        return
    
    logger.info(f"✅ user_data получен: total_score={user_data.get('total_score', 0)}")
    
    # Вычисляем уровень
    total_score = user_data.get("total_score", 0)
    score_balance = user_data.get("score_balance", 0)
    level, level_name = get_level_info(total_score)
    
    # ✅ Считаем точность из данных пользователя
    tasks_solved = user_data.get("tasks_solved", 0)
    tasks_correct = user_data.get("tasks_correct", 0)
    
    if tasks_solved > 0:
        accuracy = round((tasks_correct / tasks_solved) * 100, 1)
        accuracy_int = int(accuracy)
    else:
        accuracy = 0.0
        accuracy_int = 0
    
    if accuracy >= 90:
        accuracy_level = "🌟 Золотой уровень"
        accuracy_emoji = "🟢"
    elif accuracy >= 75:
        accuracy_level = "🥈 Серебряный уровень"
        accuracy_emoji = "🟡"
    elif accuracy >= 60:
        accuracy_level = "🥉 Бронзовый уровень"
        accuracy_emoji = "🟠"
    else:
        accuracy_level = "🌱 Ученик"
        accuracy_emoji = "🔴"
    
    # ✅ СЧИТАЕМ ТОЛЬКО 4 ОСНОВНЫХ ОСТРОВА (не boss_*, не миры)
    main_zones = ["addition", "subtraction", "multiplication", "division"]
    completed_zones = set(user_data.get("completed_zones", []))
    islands_completed = len([z for z in completed_zones if z in main_zones])
    
    # Собираем статистику
    bosses_defeated = len(user_data.get("defeated_bosses", []))
    
    # === БЕЗОПАСНОЕ ЭКРАНИРОВАНИЕ ИМЕНИ ===
    user_name = update.effective_user.first_name or "Игрок"
    user_name_safe = escape_markdown(user_name)
    
    # Генерируем текст профиля
    profile_text = (
        f"🏰 *ЗАЛ СЛАВЫ* {user_name_safe}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 *Уровень*: {level} ({level_name})\n"
        f"🏆 *Рейтинг*: {total_score:,} очков\n"
        f"💰 *Баланс*: {score_balance:,} очков\n\n"
        f"📊 *Статистика*:\n"
        f"✅ Решено задач: {tasks_solved}\n"
        f"{accuracy_emoji} Точность: {accuracy_int}% ({accuracy_level})\n"
        f"⚔️ Побеждено боссов: {bosses_defeated}/5\n"
        f"🏝️ Пройдено островов: {islands_completed}/4\n\n"
    )
    
    # Добавляем инвентарь — ✅ ПОКАЗЫВАЕМ ВСЕ ПРЕДМЕТЫ (без обрезки!)
    profile_text += "🎒 *Инвентарь*:\n"
    inventory = user_data.get("inventory", [])
    
    if inventory:
        potion_luck_count = sum(1 for item in inventory if item.lower() in ["зелье_удачи", "potion_luck"])
        
        displayed_items = set()
        item_lines = []
        
        for item_id in inventory:
            item_lower = item_id.lower()
            
            if item_lower in ["зелье_удачи", "potion_luck"]:
                if "зелье_удачи" not in displayed_items and "potion_luck" not in displayed_items:
                    item_lines.append(f"▫️ {get_item_display(item_id)} ×{potion_luck_count}")
                    displayed_items.add("зелье_удачи")
                    displayed_items.add("potion_luck")
            else:
                if item_id not in displayed_items:
                    item_display = get_item_display(item_id)
                    # ✅ Если артефакт — добавляем уровень
                    if item_id.startswith("artifact_"):
                        artifact_upgrades = user_data.get("artifact_upgrades", {})
                        level = artifact_upgrades.get(item_id, 0)
                        item_display = f"{item_display} (ур. {level})"
                    item_lines.append(f"▫️ {item_display}")
                    displayed_items.add(item_id)
        
        # ✅ ПОКАЗЫВАЕМ ВСЕ ПРЕДМЕТЫ (убрали ограничение [:7])
        for line in item_lines:
            profile_text += line + "\n"
    else:
        profile_text += "▫️ Пусто (пора исследовать Числяндию!)\n"
    
    # Добавляем трофеи в Замке
    trophies = user_data.get("castle_decorations", [])
    if trophies:
        profile_text += "\n🏰 *Трофеи в Замке*:\n"
        for trophy_id in trophies[:3]:
            profile_text += f"▫️ {get_trophy_display(trophy_id)}\n"
        if len(trophies) > 3:
            profile_text += f"▫️ ... и ещё {len(trophies) - 3} трофеев\n"
    
    profile_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Эмоциональная реакция Манюни
    manunya_phrases = [
        "*«Ты так точно решаешь задачи! Я горжусь тобой!»*",
        "*«Каждая решённая задача делает тебя сильнее!»*",
        "*«Твоя точность растёт с каждым днём!»*",
        "*«Я вижу, как ты становишься настоящим матемагом!»*",
        "*«Продолжай в том же духе — у тебя всё получится!»*"
    ]
    
    manunya_phrase = random.choice(manunya_phrases)
    profile_text += f"💬 **Манюня**: {manunya_phrase}"
    
    # Клавиатура действий
    keyboard = [
        ["🏆 Достижения", "🏰 Мой Замок"],
        ["⬅️ Назад"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    try:
        await update.message.reply_text(
            profile_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info("✅ Профиль успешно отправлен")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки профиля: {e}")
        await update.message.reply_text(
            f"⚠️ Ошибка разметки профиля. Отладка:\n```\n{escape_markdown(profile_text)}\n```",
            parse_mode="Markdown"
        )
        raise


async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает достижения игрока"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка хранилища.")
        return
    
    user_data = storage.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден.")
        return
    
    achievements = user_data.get("achievements", {})
    
    all_achievements = [
        "first_step", "fire_path", "ice_accuracy",
        "zero_victory", "shadow_victory", "multiply_victory", "fracosaur_victory", "lord_victory",
        "quick_mind", "explorer"
    ]
    
    achievements_text = "🏆 *ДОСТИЖЕНИЯ*\n"
    achievements_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for ach_id in all_achievements:
        unlocked = achievements.get(ach_id, False)
        achievements_text += get_achievement_display(ach_id, unlocked) + "\n"
    
    achievements_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━"
    achievements_text += "\n💡 *Совет*: Продолжай исследовать Числяндию, чтобы открыть новые достижения!"
    
    keyboard = [["🏰 Мой Замок", "👤 Профиль"], ["⬅️ Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        achievements_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def show_castle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает Замок игрока"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка хранилища.")
        return
    
    user_data = storage.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден.")
        return
    
    castle_text = "🏰 *МОЙ ЗАМОК*\n"
    castle_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not user_data.get("completed_normal_game", False):
        castle_text += (
            "🔒 *Замок ещё закрыт!*\n"
            "Чтобы открыть Замок, победи Истинного Владыку.\n"
            "Продолжай исследовать острова и побеждать боссов!"
        )
    else:
        castle_text += "✨ *Добро пожаловать в твой Замок!*\n"
        castle_text += "Здесь хранятся твои трофеи и награды.\n\n"
        
        trophies = user_data.get("castle_decorations", [])
        if trophies:
            castle_text += "🏆 *Твои трофеи*:\n"
            for trophy_id in trophies:
                castle_text += f"▫️ {get_trophy_display(trophy_id)}\n"
        else:
            castle_text += "▫️ Пока пусто. Побеждай боссов, чтобы получить трофеи!\n"
        
        castle_text += "\n🎭 *Обитатели Замка*:\n"
        castle_text += "▫️ ВладимИр — дворецкий (ждёт твоего прибытия)\n"
        
        defeated_bosses = user_data.get("defeated_bosses", [])
        if defeated_bosses:
            castle_text += "\n🎓 *Наставники*:\n"
            boss_names = {
                "null_void": "Нуль-Пустота",
                "minus_shadow": "Минус-Тень",
                "evil_multiplier": "Злой Умножитель",
                "fracosaur": "Дробозавр",
                "final_boss": "Финальный Владыка",
                "true_lord": "Истинный Владыка"
            }
            for boss_id in defeated_bosses:
                castle_text += f"▫️ {boss_names.get(boss_id, boss_id)} — готов учить!\n"
    
    castle_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    keyboard = [["👤 Профиль", "🏆 Достижения"], ["⬅️ Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        castle_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


# ========================================
# ✅ ФУНКЦИЯ: ИНВЕНТАРЬ (ПОКАЗЫВАЕТ ВСЕ ПРЕДМЕТЫ)
# ========================================
async def show_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает только предметы + магазин/алхимия"""
    user_id = update.effective_user.id if update.effective_user else 0
    
    storage = context.bot_data.get('storage')
    if not storage:
        await update.message.reply_text("⚠️ Ошибка: хранилище данных не инициализировано.")
        return
    
    user_data = storage.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Профиль не найден.")
        return
    
    inventory = user_data.get("inventory", [])
    
    # ✅ ИСПРАВЛЕНО: показываем score_balance (валюта) и total_score (рейтинг)
    score_balance = user_data.get("score_balance", 0)
    total_score = user_data.get("total_score", 0)
    
    # Считаем количество каждого предмета
    item_counts = Counter(inventory)
    
    # Генерируем текст
    text = "🎒 **ТВОЙ РЮКЗАК**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if inventory:
        displayed_items = set()
        for item_id in inventory:
            if item_id not in displayed_items:
                count = item_counts.get(item_id, 1)
                
                # ✅ Если артефакт — получаем уровень
                if item_id.startswith("artifact_"):
                    artifact_upgrades = user_data.get("artifact_upgrades", {})
                    level = artifact_upgrades.get(item_id, 0)
                    base_display = get_item_display(item_id)
                    item_display = f"{base_display} (ур. {level})"
                else:
                    item_display = get_item_display(item_id)
                
                if count > 1:
                    text += f"▫️ {item_display} ×{count}\n"
                else:
                    text += f"▫️ {item_display}\n"
                displayed_items.add(item_id)
    else:
        text += "▫️ Пусто (пора исследовать Числяндию!)\n"
    
    # ✅ ПОКАЗЫВАЕМ ОБА ЗНАЧЕНИЯ
    text += f"\n💰 **Баланс**: {score_balance:,} очков"
    text += f"\n🏆 **Рейтинг**: {total_score:,} очков"
    text += "\n\n💡 *Совет*: Посети Магазин или Алхимию, чтобы получить предметы!"
    
    # Клавиатура только для предметов
    keyboard = [
        ["🛒 Магазин", "⚗️ Алхимия"],
        ["⬅️ Назад"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )