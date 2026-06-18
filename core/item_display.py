"""Отображение предметов инвентаря — без зависимости от Telegram."""


def get_item_display(item_id: str) -> str:
    artifact_items = {
        "artifact_luck": {"emoji": "🍀", "name": "Артефакт Удачи", "rarity": "легендарный"},
        "artifact_power": {"emoji": "⚡", "name": "Артефакт Силы", "rarity": "легендарный"},
        "artifact_wisdom": {"emoji": "🧠", "name": "Артефакт Мудрости", "rarity": "легендарный"},
    }

    item_lower = item_id.lower()
    if item_lower in artifact_items:
        item = artifact_items[item_lower]
        return f"{item['emoji']} {item['name']} ✨"

    items = {
        "candels": {"emoji": "🕯️", "name": "Серебряные подсвечники", "rarity": "обычный"},
        "candles": {"emoji": "🕯️", "name": "Серебряные подсвечники", "rarity": "обычный"},
        "portrait_maty": {"emoji": "🖼️", "name": "Портрет Пифагора", "rarity": "обычный"},
        "portrait_math": {"emoji": "🖼️", "name": "Портрет Пифагора", "rarity": "обычный"},
        "sum_gloves": {"emoji": "🧤", "name": "Перчатки Сумматора", "rarity": "обычный"},
        "unity_stone": {"emoji": "💎", "name": "Камень Единства", "rarity": "обычный"},
        "difference_dagger": {"emoji": "🗡️", "name": "Кинжал Разности", "rarity": "обычный"},
        "subtraction_shield": {"emoji": "🛡️", "name": "Щит Вычитания", "rarity": "редкий"},
        "ancient_amulet": {"emoji": "🔮", "name": "Древний Амулет", "rarity": "редкий"},
        "accuracy_amulet": {"emoji": "📿", "name": "Амулет Точности", "rarity": "редкий"},
        "magic_hat": {"emoji": "🎩", "name": "Волшебная Шляпа", "rarity": "редкий"},
        "math_crown": {"emoji": "👑", "name": "Корона Матемага", "rarity": "легендарный"},
        "bravery_potion": {"emoji": "🧪", "name": "Зелье Смелости", "rarity": "редкий"},
        "chaos_cup": {"emoji": "🍷", "name": "Кубок Хаоса", "rarity": "эпический"},
        "dice_of_fate": {"emoji": "🎲", "name": "Кубик Судьбы", "rarity": "эпический"},
        "madness_potion": {"emoji": "💀", "name": "Зелье Безумия", "rarity": "легендарный"},
        "звезда_сложения": {"emoji": "⭐", "name": "Звезда Сложения", "rarity": "обычный"},
        "амулет_вычитания": {"emoji": "🔮", "name": "Амулет Вычитания", "rarity": "обычный"},
        "мантия_умножения": {"emoji": "✨", "name": "Мантия Умножения", "rarity": "редкий"},
        "щит_деления": {"emoji": "🛡️", "name": "Щит Деления", "rarity": "редкий"},
        "корона_матемага": {"emoji": "👑", "name": "Корона Матемага", "rarity": "легендарный"},
        "золотая_морковка": {"emoji": "🥕", "name": "Золотая Морковка", "rarity": "особый"},
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
        "statue_null": {"emoji": "🗿", "name": "Статуя Нуль-Пустоты", "rarity": "особый"},
        "mirror_shadow": {"emoji": "🪞", "name": "Зеркало Теней", "rarity": "особый"},
        "tree_multiply": {"emoji": "🌳", "name": "Дерево Множеств", "rarity": "особый"},
        "fountain_fracosaur": {"emoji": "🌊", "name": "Фонтан Дробей", "rarity": "особый"},
        "статуя_нуля": {"emoji": "🗿", "name": "Статуя Нуль-Пустоты", "rarity": "особый"},
        "зеркало_теней": {"emoji": "🪞", "name": "Зеркало Теней", "rarity": "особый"},
        "дерево_множеств": {"emoji": "🌳", "name": "Дерево Множеств", "rarity": "особый"},
        "фонтан_дробей": {"emoji": "🌊", "name": "Фонтан Дробей", "rarity": "особый"},
        "песочные_часы": {"emoji": "⏳", "name": "Песочные часы", "rarity": "редкий"},
        "линейка_вечности": {"emoji": "📏", "name": "Линейка вечности", "rarity": "редкий"},
        "ключ_логики": {"emoji": "🗝️", "name": "Ключ логики", "rarity": "редкий"},
        "сердце_числяндии": {"emoji": "💖", "name": "Сердце Числяндии", "rarity": "легендарный"},
    }

    item = items.get(item_lower)
    if item:
        rarity_emoji = {
            "обычный": "",
            "редкий": "🌟",
            "эпический": "💜",
            "легендарный": "✨",
            "особый": "💫",
        }
        rarity_tag = rarity_emoji.get(item["rarity"], "")
        return f"{item['emoji']} {item['name']} {rarity_tag}".strip()

    if item_lower.startswith("artifact_"):
        artifact_names = {
            "artifact_luck": "🍀 Артефакт Удачи",
            "artifact_power": "⚡ Артефакт Силы",
            "artifact_wisdom": "🧠 Артефакт Мудрости",
        }
        name = artifact_names.get(item_lower, item_id.replace("_", " ").title())
        return f"{name} ✨"

    return f"📦 {item_id.replace('_', ' ').title()}"
