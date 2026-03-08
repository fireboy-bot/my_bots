# core/ui_helpers.py
"""
UI-хелперы для бота «Числяндия».
Версия: 1.3 (Игровая клавиатура + Банк + Замок) 🎮💡🏦🏰
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_persistent_keyboard(user_data: dict = None, menu: str = None) -> ReplyKeyboardMarkup:
    """
    Возвращает постоянное нижнее меню с кнопками.
    
    Args:
        user_data: Данные пользователя (для проверки прогресса)
        menu: Название меню (пока не используется, зарезервировано)
    """
    
    # Базовые кнопки (всегда видны)
    row1 = [
        KeyboardButton("🎮 Играть"),
        KeyboardButton("🎒 Инвентарь"),
    ]
    
    row2 = [
        KeyboardButton("👤 Профиль"),
        KeyboardButton("🛒 Магазин"),
    ]
    
    # ✅ КНОПКИ ЭКОНОМИКИ (всегда видны для Морковки!)
    row3 = [
        KeyboardButton("🏦 Златочёт"),
        KeyboardButton("🏰 Замок"),
    ]
    
    keyboard = [row1, row2, row3]
    
    # Кнопка помощи (всегда)
    row_help = [KeyboardButton("❓ Помощь")]
    keyboard.append(row_help)
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери действие..."
    )


def get_game_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для игрового процесса (только Подсказка и Назад).
    Скрывает основное меню во время решения задач.
    """
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("💡 Подсказка"), KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_boss_keyboard_layout() -> ReplyKeyboardMarkup:
    """
    Клавиатура для боя с боссом (только Назад).
    """
    return ReplyKeyboardMarkup(
        [[KeyboardButton("⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой «Назад»"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура «Да/Нет» для подтверждений"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")],
            [KeyboardButton("⬅️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_numeric_keyboard() -> ReplyKeyboardMarkup:
    """Цифровая клавиатура для ввода чисел"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3")],
            [KeyboardButton("4"), KeyboardButton("5"), KeyboardButton("6")],
            [KeyboardButton("7"), KeyboardButton("8"), KeyboardButton("9")],
            [KeyboardButton("⬅️ Назад"), KeyboardButton("0"), KeyboardButton("✅ Готово")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_task_keyboard(tasks: list, prefix: str = "task") -> InlineKeyboardMarkup:
    """
    Генерирует inline-клавиатуру с вариантами ответов для задачи.
    """
    keyboard = []
    
    for i, task in enumerate(tasks):
        row = []
        for j, option in enumerate(task.get("options", [])):
            callback_data = f"{prefix}_{i}_{j}"
            row.append(InlineKeyboardButton(str(option), callback_data=callback_data))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⏭ Пропустить", callback_data=f"{prefix}_skip")])
    
    return InlineKeyboardMarkup(keyboard)


def get_boss_keyboard(boss_tasks: list, boss_id: str) -> InlineKeyboardMarkup:
    """
    Генерирует inline-клавиатуру для боя с боссом.
    """
    keyboard = []
    
    for i, task in enumerate(boss_tasks):
        row = []
        for j, option in enumerate(task.get("options", [])):
            callback_data = f"boss_{boss_id}_{i}_{j}"
            row.append(InlineKeyboardButton(str(option), callback_data=callback_data))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🏳️ Сдаться", callback_data=f"boss_{boss_id}_surrender")])
    
    return InlineKeyboardMarkup(keyboard)


def get_hint_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """
    Кнопка «💡 Подсказка» для задач.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💡 Подсказка (-10 очков)", callback_data=f"hint_{task_id}")]
    ])