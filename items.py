# items.py
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
    }
}