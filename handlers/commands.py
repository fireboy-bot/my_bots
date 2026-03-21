# handlers/commands.py
"""
Обработчики команд бота.
Версия: 3.2 (All Syntax Fixed) 🎬✨✅

Изменения:
- ✅ Все type hints исправлены (user_ dict → user_data: dict)
- ✅ Все .get() вызовы завершены
- ✅ Кинематографичный вход работает
"""

import asyncio
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from core.logger import log_user_action
from core.ui_helpers import get_persistent_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — кинематографичный вход в Числяндию"""
    
    # ✅ Получаем адаптер платформы
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер платформы не инициализирован.")
        return
    
    # ✅ Нормализуем user_id к строке (для совместимости с MAX)
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    first_name = update.effective_user.first_name if update.effective_user else "Путешественник"
    
    log_user_action(user_id, "START", f"name='{first_name}'")
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище данных не инициализировано.")
        return
    
    # ✅ Используем get_or_create_user для новых пользователей
    user_data = storage.get_or_create_user(
        user_id, 
        update.effective_user.username if update.effective_user else None,
        first_name
    )
    
    # Вычисляем уровень
    total_score = user_data.get("total_score", 0)
    level = user_data.get("level", 1)
    
    # Звания
    level_names = {
        1: "Ученик", 6: "Исследователь", 11: "Матемаг",
        16: "Хранитель Чисел", 21: "Владыка Числяндии"
    }
    level_name = "Ученик"
    for lvl_threshold, name in level_names.items():
        if level >= lvl_threshold:
            level_name = name
    
    # ✅ СЧИТАЕМ ТОЛЬКО 4 ОСНОВНЫХ ОСТРОВА
    main_zones = ["addition", "subtraction", "multiplication", "division"]
    completed_zones = set(user_data.get("completed_zones", []))
    islands_completed = len([z for z in completed_zones if z in main_zones])
    
    # Статистика
    tasks_solved = user_data.get("tasks_solved", 0)
    bosses_defeated = len(user_data.get("defeated_bosses", []))
    
    # Проверяем первый запуск
    is_first_time = user_data.get("first_time", True)
    
    # Клавиатура (будет показана в конце)
    keyboard = get_persistent_keyboard(user_data, menu="main")
    
    if is_first_time:
        # 🎬 КИНЕМАТОГРАФИЧНЫЙ ВХОД (для новых игроков)
        
        # Сообщение 1: Атмосфера
        await adapter.send_message(
            user_id=user_id,
            text="…\n\n*Ты открываешь глаза…*",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.2)
        
        # Сообщение 2: Загадка
        await adapter.send_message(
            user_id=user_id,
            text="*Вокруг — странное место…*\n\n"
                 "Числа… будто живые.\n"
                 "Они двигаются.\n"
                 "Меняются.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.2)
        
        # Сообщение 3: Знакомство с Манюней
        await adapter.send_message(
            user_id=user_id,
            text="*И вдруг…*\n\n"
                 "🧚‍♀️ *«О! Ты наконец-то пришёл!»*\n\n"
                 "Меня зовут Манюня.\n"
                 "Я ждала тебя.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.2)
        
        # Сообщение 4: Мир Числяндии
        await adapter.send_message(
            user_id=user_id,
            text="*Здесь — Числяндия.*\n"
                 "Мир, где числа — это не просто цифры.\n\n"
                 "Они могут ошибаться.\n"
                 "И… *ты можешь их исправить.* ✨",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.2)
        
        # Сообщение 5: Возможности
        await adapter.send_message(
            user_id=user_id,
            text="🏝️ *Здесь есть острова.*\n"
                 "⚔️ *Есть сущности, которые проверяют тебя.*\n"
                 "🎒 *Есть вещи, которые помогут тебе стать сильнее.*\n\n"
                 "Но самое важное…",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1.2)
        
        # Сообщение 6: Крючок + призыв к действию + клавиатура
        welcome_final = (
            f"✨ *Ты не просто игрок.*\n"
            f"Ты — тот, кто может *понять* этот мир.\n\n"
            f"Нажми 🗺️ *Мир*.\n"
            f"Посмотрим, что ты умеешь 🙂"
        )
        
        await adapter.send_message(
            user_id=user_id,
            text=welcome_final,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # ✅ Помечаем что первый вход пройден
        user_data["first_time"] = False
        storage.save_user(user_id, user_data)
        
        log_user_action(user_id, "START_FIRST_TIME")
        
    else:
        # 🔄 ОБЫЧНЫЙ ВХОД (для вернувшихся игроков)
        
        # Персонализированное приветствие
        if bosses_defeated >= 7:  # Все боссы побеждены
            greeting = f"👋 *С возвращением, {first_name}!*\n\n"
            greeting += "🏆 *Легенда Числяндии!*\n"
            greeting += "Ты освободил мир чисел.\n"
            greeting += "Что будешь делать сегодня?\n\n"
            greeting += "🗝️ Тайная комната ждёт новых открытий…"
        elif bosses_defeated > 0:
            greeting = f"👋 *С возвращением, {first_name}!*\n\n"
            greeting += f"📊 Твой уровень: {level} ({level_name})\n"
            greeting += f"⭐ Очки: {total_score:,}\n"
            greeting += f"✅ Решено задач: {tasks_solved}\n"
            greeting += f"🏝️ Пройдено островов: {islands_completed}/4\n"
            greeting += f"⚔️ Побеждено боссов: {bosses_defeated}/5\n\n"
            greeting += "Продолжим приключение?"
        else:
            greeting = f"👋 *С возвращением, {first_name}!*\n\n"
            greeting += f"📊 Твой уровень: {level} ({level_name})\n"
            greeting += "🗺️ *Мир* ждёт тебя.\n"
            greeting += "🎒 *Инвентарь* хранит твои находки.\n"
            greeting += "🏰 *Замок* — твоя крепость.\n\n"
            greeting += "С чего начнём?"
        
        await adapter.send_message(
            user_id=user_id,
            text=greeting,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        log_user_action(user_id, "START_RETURNING")


async def show_bosses_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает гид по боссам"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    guide_text = (
        "⚔️ *ГИД ПО БОССАМ ЧИСЛЯНДИИ*\n\n"
        "🌑 **Нуль-Пустота** (Остров Сложения)\n"
        "   Способность: Обнуляет очки\n\n"
        "🌑 **Минус-Тень** (Пещера Вычитания)\n"
        "   Способность: Крадёт очки при ошибке\n\n"
        "🌀 **Злой Умножитель** (Лес Умножения)\n"
        "   Способность: Удваивает задачи\n\n"
        "🌊 **Дробозавр** (Река Деления)\n"
        "   Способность: Делит очки пополам\n\n"
        "👑 **Финальный Владыка** (Тронный Зал)\n"
        "   Способность: Все способности сразу!\n\n"
        "💡 *Совет*: Собери все артефакты перед финальным боем!"
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=guide_text,
        parse_mode="Markdown"
    )


async def restart_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск игры (сброс прогресса)"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка хранилища.")
        return
    
    user_data = storage.get_user(user_id)
    if not user_data:
        await adapter.send_message(user_id, "❌ Профиль не найден.")
        return
    
    # Подтверждение
    keyboard = [["✅ Да, сбросить"], ["❌ Отмена"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await adapter.send_message(
        user_id=user_id,
        text=(
            "⚠️ *ВНИМАНИЕ!* Это действие необратимо!\n\n"
            "Весь прогресс будет потерян:\n"
            "• Очки и уровень\n"
            "• Пройденные острова\n"
            "• Побеждённые боссы\n"
            "• Инвентарь и достижения\n\n"
            "Вы уверены?"
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает последние логи (только для админа)"""
    from config import ADMIN_IDS
    
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    if user_id not in [str(x) for x in ADMIN_IDS]:
        await adapter.send_message(user_id, "🔒 Только для администратора!")
        return
    
    try:
        with open('logs/bot.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()[-20:]  # Последние 20 строк
        
        log_text = "📋 *ПОСЛЕДНИЕ ЛОГИ*:\n\n"
        log_text += "```\n"
        log_text += "".join(logs)
        log_text += "```"
        
        await adapter.send_message(
            user_id=user_id,
            text=log_text,
            parse_mode="Markdown"
        )
    except FileNotFoundError:
        await adapter.send_message(user_id, "⚠️ Лог-файл не найден!")
    except Exception as e:
        await adapter.send_message(user_id, f"❌ Ошибка: {e}")


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка состояния бота"""
    import time
    import os
    import glob
    from config import ADMIN_IDS
    
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    if user_id not in [str(x) for x in ADMIN_IDS]:
        await adapter.send_message(user_id, "🔒 Только для администратора!")
        return
    
    status_text = "🏥 *СОСТОЯНИЕ БОТА*:\n\n"
    
    # ✅ Время работы
    start_time = context.bot_data.get('start_time')
    if start_time:
        uptime = int(time.time() - start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        status_text += f"⏱️ *Время работы*: {hours}ч {minutes}м\n"
    
    # ✅ База данных
    try:
        storage = context.bot_data.get('storage')
        if storage:
            users = storage.get_all_users()
            status_text += f"🗄️ *База данных*: OK ({len(users)} пользователей)\n"
        else:
            status_text += "🗄️ *База данных*: ⚠️ Не инициализирована\n"
    except Exception as e:
        status_text += f"🗄️ *База данных*: ❌ {e}\n"
    
    # ✅ Кэш аватарок
    cache_file = os.path.join('data', 'avatar_cache.json')
    if os.path.exists(cache_file):
        status_text += f"🖼️ *Кэш аватарок*: OK\n"
    else:
        status_text += f"🖼️ *Кэш аватарок*: ⚠️ Не найден\n"
    
    # ✅ Бэкапы
    backups = glob.glob(os.path.join('data', 'progress_backup_*.db'))
    status_text += f"💾 *Бэкапы*: {len(backups)} файлов\n"
    
    status_text += "\n✅ *Бот работает нормально!*"
    
    await adapter.send_message(
        user_id=user_id,
        text=status_text,
        parse_mode="Markdown"
    )