# core/vladimir_persona.py
"""
ВладимИр — дворецкий Числяндии.
Версия: 1.0 (Persona + Avatar Structure) 🎩🫖
"""

# === АВАТАРКИ (заглушки — мама Морковки добавит файлы) ===
VLADIMIR_AVATARS = {
    "calm": "images/vladimir_calm.jpg",        # ✅ Основная (уже есть)
    "approve": "images/vladimir_approve.jpg",  # 🔄 Для покупок/улучшений
    "disappointed": "images/vladimir_disappointed.jpg",  # 🔄 Для ошибок
    "proud": "images/vladimir_proud.jpg",      # 🔄 Для побед
    "thinking": "images/vladimir_thinking.jpg",  # 🔄 Для подсказок
    "relaxed": "images/vladimir_relaxed.jpg",  # 🔄 Для секретных диалогов
}


def get_vladimir_avatar(mood: str = "calm") -> str:
    """
    Возвращает путь к аватарке Владимира по настроению.
    Если файл не найден — возвращает основную (calm).
    """
    return VLADIMIR_AVATARS.get(mood, VLADIMIR_AVATARS["calm"])


# === БАЗОВЫЕ ФРАЗЫ (заглушка — основные в JSON) ===
VLADIMIR_BASE_PHRASES = {
    "greeting": [
        "🎩 «Добро пожаловать в Ваш Замок, сударыня.»",
        "🎩 «ВладимИр к Вашим услугам. Чем могу быть полезен?»",
    ],
    "locked": [
        "🎩 «Замок закрыт, сударыня. Сначала победите Финального Владыку.»",
        "🎩 «Я буду ждать... с чаем. И совком.»",
    ],
}


def get_vladimir_phrase(context: str) -> str:
    """Возвращает случайную фразу по контексту"""
    import random
    phrases = VLADIMIR_BASE_PHRASES.get(context, VLADIMIR_BASE_PHRASES["greeting"])
    return random.choice(phrases)


# === ЭКСПОРТ ===
__all__ = [
    "VLADIMIR_AVATARS",
    "get_vladimir_avatar",
    "get_vladimir_phrase",
]