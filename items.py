# items.py
"""
Предметы и артефакты Числяндии.
Версия: 2.1 (Castle Decorations Upgrade Config) 🎮⚖️🏰
"""

# ============================================
# 🛒 МАГАЗИН: ПРЕДМЕТЫ (СУЩЕСТВУЮЩИЕ)
# ============================================

SHOP_ITEMS = {
    # === ОСТРОВ СЛОЖЕНИЯ ===
    "sum_gloves": {
        "name": "Перчатки Сумматора",
        "description": "За каждую задачу на сложение даёт +3 очка (накопительно)!",
        "type": "island_bound_temporary",
        "effect": "additive_progressive",
        "value": 3,
        "cost_in_score": 50
    },
    "unity_stone": {
        "name": "Камень Единства",
        "description": "За задачи со сложением одинаковых чисел (5+5) ты получишь ×2 очков!",
        "type": "island_bound_temporary",
        "effect": "double_on_equal_operands",
        "cost_in_score": 70
    },
    
    # === ОСТРОВ ВЫЧИТАНИЯ ===
    "difference_dagger": {
        "name": "Кинжал Разности",
        "description": "При ошибке в вычитании ты вернёшь 50% штрафа!",
        "type": "island_bound_temporary",
        "effect": "partial_penalty_refund",
        "refund_ratio": 0.5,
        "cost_in_score": 80
    },
    "subtraction_shield": {
        "name": "Щит Вычитания",
        "description": "Первая ошибка на уровне вычитания будет прощена!",
        "type": "island_bound_temporary",
        "effect": "ignore_first_mistake",
        "cost_in_score": 120
    },
    "ancient_amulet": {
        "name": "Древний Амулет",
        "description": "Если пройдёшь уровень вычитания без ошибок — получишь +100 очков за босса!",
        "type": "island_bound_temporary",
        "effect": "perfect_run_bonus",
        "bonus": 100,
        "cost_in_score": 150
    },
    
    # === УНИВЕРСАЛЬНЫЕ ПРЕДМЕТЫ ===
    "accuracy_amulet": {
        "name": "Амулет Точности",
        "description": "Подсказки теперь бесплатны!",
        "type": "permanent",
        "effect": "hint_is_free",
        "cost_in_score": 200
    },
    "magic_hat": {
        "name": "Волшебная Шляпа",
        "description": "Ошибки больше не штрафуют!",
        "type": "permanent",
        "effect": "ignore_mistake_penalty",
        "cost_in_score": 250
    },
    
    # === СПЕЦИАЛЬНЫЕ ПРЕДМЕТЫ ===
    "math_crown": {
        "name": "Корона Матемага",
        "description": "Активирует все бонусы: бесплатные подсказки, игнорирование штрафов, увеличенные очки и XP!",
        "type": "permanent",
        "effect": "math_crown",
        "cost_in_score": 500
    },
    
    # === АЛХИМИЧЕСКИЕ ПРЕДМЕТЫ ===
    "bravery_potion": {
        "name": "Зелье Смелости",
        "description": "Следующая задача: +50 за успех, −30 за ошибку!",
        "type": "one_time_risk",
        "effect": "risk_reward",
        "success_bonus": 50,
        "failure_penalty": -30,
        "cost_in_score": 150
    },
    "chaos_cup": {
        "name": "Кубок Хаоса",
        "description": "Следующая задача: +100 за успех, −80 за ошибку!",
        "type": "one_time_risk",
        "effect": "chaos",
        "success_reward": 100,
        "failure_penalty": -80,
        "cost_in_score": 250
    },
    "dice_of_fate": {
        "name": "Кубик Судьбы",
        "description": "Перед следующей задачей будет брошен кубик судьбы!",
        "type": "one_time_risk",
        "effect": "dice_roll",
        "cost_in_score": 180
    },
    "madness_potion": {
        "name": "Зелье Безумия",
        "description": "На этом уровне: ошибки = +20, правильные = −10. Отменить можно за 100 очков.",
        "type": "level_wide_risk",
        "effect": "inverted_scoring",
        "error_reward": 20,
        "correct_reward": -10,
        "cancel_cost": 100,
        "cost_in_score": 200
    },
}

# ============================================
# 🔮 АРТЕФАКТЫ: ДОЛГОСРОЧНАЯ ПРОКАЧКА
# ============================================
# Баланс: ощутимо, но не имба. Капы не ломают экономику.
# ============================================

ARTIFACTS = {
    # 🍀 АРТЕФАКТ УДАЧИ
    "artifact_luck": {
        "id": "artifact_luck",
        "name": "🍀 Артефакт Удачи",
        "description": "Постоянный бонус к очкам за правильные ответы",
        "type": "artifact",
        "base_price": 500,  # Цена покупки (уровень 1)
        "max_level": 10,
        "effect": "score_bonus",
        "base_value": 0.05,      # +5% на 1 уровне
        "per_level": 0.05,       # +5% за уровень
        "max_value": 0.40,       # ⚠️ КАП: +40% (не имба!)
        "cost_multiplier": 1.4,  # Стоимость растёт экспоненциально
        "requires_upkeep": True, # Не работает без оплаты замка
        "icon": "🍀"
    },
    
    # ⚡ АРТЕФАКТ СИЛЫ
    "artifact_power": {
        "id": "artifact_power",
        "name": "⚡ Артефакт Силы",
        "description": "Снижение потери очков при ошибке",
        "type": "artifact",
        "base_price": 500,
        "max_level": 10,
        "effect": "penalty_reduction",
        "base_value": 0.10,      # -10% штрафа на 1 уровне
        "per_level": 0.10,       # -10% за уровень
        "max_value": 0.75,       # ⚠️ КАП: -75% (всё ещё больно!)
        "min_penalty": 2,        # ⚠️ МИНИМУМ: всегда -2 очка при ошибке
        "cost_multiplier": 1.4,
        "requires_upkeep": True,
        "icon": "⚡"
    },
    
    # 🧠 АРТЕФАКТ МУДРОСТИ
    "artifact_wisdom": {
        "id": "artifact_wisdom",
        "name": "🧠 Артефакт Мудрости",
        "description": "Дополнительные подсказки в бою с боссом",
        "type": "artifact",
        "base_price": 750,
        "max_level": 10,
        "effect": "boss_hints",
        "base_value": 1,         # +1 подсказка на 1 уровне
        "per_level": 1,          # +1 за уровень
        "max_value": 10,         # Максимум подсказок в запасе
        "max_per_battle": 3,     # ⚠️ КАП: не более 3 за один бой
        "cost_multiplier": 1.45,
        "requires_upkeep": True,
        "icon": "🧠"
    },
}

# ============================================
# ⚙️ КОНФИГУРАЦИЯ ДЛЯ ARTIFACT_MANAGER
# ============================================

ARTIFACT_CONFIG = {
    "artifact_luck": {
        "name": "🍀 Артефакт Удачи",
        "base_price": 500,
        "effect": "score_bonus",
        "base_value": 0.05,
        "per_level": 0.05,
        "max_value": 0.40,       # ⚠️ КАП +40%
        "cost_multiplier": 1.4,
        "requires_upkeep": True
    },
    "artifact_power": {
        "name": "⚡ Артефакт Силы",
        "base_price": 500,
        "effect": "penalty_reduction",
        "base_value": 0.10,
        "per_level": 0.10,
        "max_value": 0.75,       # ⚠️ КАП -75%
        "min_penalty": 2,        # ⚠️ МИНИМУМ -2 очка
        "cost_multiplier": 1.4,
        "requires_upkeep": True
    },
    "artifact_wisdom": {
        "name": "🧠 Артефакт Мудрости",
        "base_price": 750,
        "effect": "boss_hints",
        "base_value": 1,
        "per_level": 1,
        "max_value": 10,
        "max_per_battle": 3,     # ⚠️ КАП 3 за бой
        "cost_multiplier": 1.45,
        "requires_upkeep": True
    },
}

# ============================================
# 🏰 ДЕКОРАЦИИ ЗАМКА — ПОЛНАЯ КОНФИГУРАЦИЯ
# ============================================
# Баланс: +2% за уровень, кап +10% на декорацию
# 8 декораций × 10% = макс. +80% к очкам от замка
# ============================================

CASTLE_DECORATIONS = [
    {
        "id": "carrot_wall",
        "name": "🥕 Морковки на стене",
        "base_price": 300,
        "tier": 1,
        "max_level": 10,
        "bonus_per_level": 0.02,   # +2% за уровень
        "max_bonus": 0.10,         # ⚠️ КАП: +10%
        "cost_multiplier": 1.4,    # Стоимость растёт экспоненциально
        "description": "Сладкие морковки украшают стены!",
        "emoji": "🥕"
    },
    {
        "id": "candles",
        "name": "🕯️ Серебряные подсвечники",
        "base_price": 400,
        "tier": 1,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Серебряный свет освещает залы!",
        "emoji": "🕯️"
    },
    {
        "id": "portrait_math",
        "name": "🖼️ Портрет Пифагора",
        "base_price": 500,
        "tier": 1,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Великий математик вдохновляет тебя!",
        "emoji": "🖼️"
    },
    {
        "id": "formula_wallpaper",
        "name": "📐 Обои «Сад формул»",
        "base_price": 1500,
        "tier": 2,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Формулы растут как цветы в саду!",
        "emoji": "📐"
    },
    {
        "id": "chandelier",
        "name": "💡 Хрустальная люстра",
        "base_price": 2500,
        "tier": 2,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Хрусталь переливается всеми цветами!",
        "emoji": "💡"
    },
    {
        "id": "textbook_throne",
        "name": "🪑 Трон из учебников",
        "base_price": 3000,
        "tier": 2,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Трон мудрости для настоящего матемага!",
        "emoji": "🪑"
    },
    {
        "id": "star_dome",
        "name": "🌟 Звёздный купол",
        "base_price": 7500,
        "tier": 3,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Звёзды светят над твоим замком!",
        "emoji": "🌟"
    },
    {
        "id": "vladimir_monocle",
        "name": "🎩 Монокль Владимира",
        "base_price": 20000,
        "tier": 3,
        "max_level": 10,
        "bonus_per_level": 0.02,
        "max_bonus": 0.10,
        "cost_multiplier": 1.4,
        "description": "Легендарный монокль дворецкого!",
        "emoji": "🎩"
    },
]

# ============================================
# 📊 СВОДНАЯ ТАБЛИЦА БАЛАНСА
# ============================================
#
# 🍀 УДАЧА (10 уровней):
# • Уровень 1: +5%  | Стоимость: 500
# • Уровень 5: +25% | Накоплено: ~6,250
# • Уровень 10: +40% ⚠️ КАП | Накоплено: ~18,000
#
# ⚡ СИЛА (10 уровней):
# • Уровень 1: -10% штрафа | Стоимость: 500
# • Уровень 5: -50% штрафа | Накоплено: ~6,250
# • Уровень 10: -75% ⚠️ КАП, мин. -2 очка | Накоплено: ~18,000
#
# 🧠 МУДРОСТЬ (10 уровней):
# • Уровень 1: +1 подсказка | Стоимость: 750
# • Уровень 5: +5 подсказок | Накоплено: ~9,000
# • Уровень 10: +10 подсказок, макс. 3/бой | Накоплено: ~25,000
#
# 🏰 ЗАМОК (8 декораций × 10 уровней):
# • Каждая декорация: +2% за уровень, кап +10%
# • Полный замок: +80% к очкам
# • Стоимость полной прокачки: ~1,863,540 золота
# • Endgame контент для самых преданных!
#
# 💰 ИТОГО на артефакты: ~61,000 золота
# 🏰 ИТОГО на замок: ~1,863,540 золота
# 📈 В задачах: ~37,270 задач для полного замка
# ⏱️ При 50 задачах/день: ~2 года (эндгейм!)
# ============================================