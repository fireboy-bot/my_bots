[#020]
Привет. Файл `handlers/alchemy.py` получил. Это модуль «Лавки Безумца» — алхимические рецепты, рисковые артефакты и механика «всё или ничего».

Ниже — готовая документация. Просто сохрани в `docs/HANDLERS_ALCHEMY.md`.

---

## 📄 Файл: `docs/HANDLERS_ALCHEMY.md`

```markdown
# ⚗️ Alchemy Handler — Лавка Безумца

> **Файл:** `handlers/alchemy.py`  
> **Версия:** 3.2 (Fix: spend_score is NOT async) 🗄️⚗️🎩✅  
> **Ответственность:** Создание рисковых артефактов, управление рецептами, механика «всё или ничего»

---

## 📋 Обзор

`alchemy.py` — модуль, отвечающий за систему алхимии в «Числяндии». Позволяет игрокам создавать особые артефакты с рисковыми эффектами в обмен на золотые.

**Ключевые особенности:**
| Фича | Описание |
|------|----------|
| 🔓 Прогрессивная разблокировка | Рецепты открываются по мере прохождения миров |
| 💰 Оплата через ScoreManager | Единая система списания очков |
| ⚠️ Рисковые эффекты | Артефакты с механикой «большой риск — большая награда» |
| 🎭 Интеграция с Владимиром | Комментарии персонажа при создании (если замок открыт) |
| 🔘 Inline-кнопки | Интерактивный интерфейс под сообщением |

```
Пользователь: /alchemy
         │
         ▼
┌─────────────────┐
│   show_alchemy()│
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
get_     get_
available_ alchemy_
recipes() inline_...()
    │         │
    ▼         ▼
Проверка   Генерация
прогресса  кнопок
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│ handle_         │
│ alchemy_callback│ ← Нажатие кнопки
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ execute_craft() │ ← Создание артефакта
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
Списание   + в
очков    inventory
```

---

## ⚙️ Конфигурация рецептов (`ALCHEMY_RECIPES`)

Встроенный словарь с параметрами всех алхимических рецептов.

```python
ALCHEMY_RECIPES = {
    "bravery_potion": {
        "cost_in_score": 150,
        "unlocks_after": "subtraction"  # Открывается после мира "Вычитание"
    },
    "chaos_cup": {
        "cost_in_score": 250,
        "unlocks_after": "multiplication"
    },
    "dice_of_fate": {
        "cost_in_score": 180,
        "unlocks_after": "division"
    },
    "madness_potion": {
        "cost_in_score": 200,
        "unlocks_after": "completed_normal_game"  # После победы над Финальным Владыкой
    }
}
```

**Типы условий разблокировки:**
| Значение `unlocks_after` | Условие |
|-------------------------|---------|
| `None` | Доступно сразу |
| `"subtraction"` | Мир «Вычитание» разблокирован |
| `"multiplication"` | Мир «Умножение» разблокирован |
| `"division"` | Мир «Деление» разблокирован |
| `"completed_normal_game"` | Победа над Финальным Владыкой |

---

## 🔧 Основные функции

### `get_available_recipes(progress: dict) -> List[str]`
Возвращает список ID рецептов, доступных игроку.

**Логика:**
```
1. Получить unlocked_zones из progress
2. Проверить completed_normal_game
3. Для каждого рецепта:
   ├─ Если unlocks_after == None → доступен
   ├─ Если условие в unlocked_zones → доступен
   └─ Иначе → скрыт
4. Вернуть список доступных ID
```

**Пример:**
```python
progress = {"unlocked_zones": ["addition", "subtraction"], "completed_normal_game": False}
available = get_available_recipes(progress)
# → ["bravery_potion"]  # только зелье смелости
```

---

### `get_alchemy_inline_keyboard(available_items, current_balance) -> InlineKeyboardMarkup`
Генерирует inline-кнопки под сообщением для создания артефактов.

**Формат кнопки:**
```
✅ Создать {name} ({cost})  → callback_data: "craft_{item_id}"
❌ {name} ({cost}) — недоступно  → callback_data: "noop"
```

**Особенности:**
- Кнопка «Назад в игру» с `callback_data="back_to_game"`
- Проверка баланса: если `current_balance < cost` → кнопка неактивна
- Использует `InlineKeyboardMarkup` для отправки под сообщением

---

### `show_alchemy(update, context)` 🎯
Отображает интерфейс Лавки Безумца с аватаркой Алхимика.

**Алгоритм:**
```
1. Получить user_id и storage из context
2. Загрузить progress игрока
3. Получить доступные рецепты через get_available_recipes()
4. Сформировать сообщение:
   ├─ Заголовок и баланс
   ├─ Список рецептов с ценами и описаниями
   ├─ Подсказки по разблокировке
   └─ Инструкция по созданию
5. Сгенерировать inline-клавиатуру
6. Отправить аватарку Алхимика через send_character_message()
7. Отправить сообщение с клавиатурой
```

**Пример сообщения:**
```
💀 **ЛАВКА БЕЗУМЦА**

💰 Твой баланс: *1250 золотых*
🏆 Твой рейтинг: *3420 очков*

ХА-ХА-ХА! Добро пожаловать в мою лабораторию хаоса!
Преврати свои очки в безумные артефакты... если осмелишься!

✅ **Зелье Смелости**
   💰 Цена: 150 золотых
   ℹ️ Увеличивает награду за риск, но удваивает штраф за ошибку

❌ **Кубик Судьбы** (180) — недоступно
   ℹ️ Случайный множитель награды или штрафа

📌 **Как создать?**
Нажми на кнопку под сообщением!
```

---

### `execute_craft(user_id, item_id, storage, score_manager) -> Tuple[bool, str]` 🎯
Выполняет создание артефакта: проверка условий, списание очков, добавление в инвентарь.

**Параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `user_id` | `int` | ID пользователя |
| `item_id` | `str` | ID создаваемого предмета |
| `storage` | `PlayerStorage` | Интерфейс для работы с БД |
| `score_manager` | `ScoreManager` | Менеджер очков (опционально) |

**Возвращает:** `(success: bool, message: str)`

**Алгоритм:**
```
1. Загрузить progress и inventory игрока
2. Проверить существование рецепта в ALCHEMY_RECIPES
3. Проверить существование предмета в SHOP_ITEMS
4. Проверить баланс: current_balance >= cost_in_score
5. Проверить тип предмета:
   ├─ Если one_time_risk / level_wide_risk и уже в inventory → ошибка
6. Проверить разблокировку: item_id in get_available_recipes(progress)
7. Списать очки:
   ├─ Если есть score_manager → использовать score_manager.spend_score()  ← БЕЗ await!
   ├─ Иначе → прямое обновление progress["score_balance"]
8. Добавить item_id в inventory (если ещё нет)
9. Сохранить progress через storage.save_user()
10. Вернуть (True, "✨ Создано: {name}!")
```

> ⚠️ **Важно:** `score_manager.spend_score()` — **не асинхронный** метод! Не использовать `await`.

---

### `get_alchemy_activation_message(item_id: str) -> str`
Возвращает форматированное сообщение об активации эффекта артефакта.

**Поддерживаемые типы эффектов:**

| `item_type` | `item_effect` | Сообщение |
|-------------|--------------|-----------|
| `one_time_risk` | `risk_reward` | «+X за успех, -Y за ошибку на следующей задаче» |
| `one_time_risk` | `chaos` | «+X за успех, -Y за ошибку (случайный множитель)» |
| `one_time_risk` | `dice_roll` | «Бросок кубика судьбы перед следующей задачей» |
| `level_wide_risk` | `inverted_scoring` | «Ошибки = +X, правильные = 0 до конца уровня» |

**Пример возврата:**
```
✨ Ты создала **Зелье Смелости**!

⚠️ *Эффект сработает на следующей задаче!*

💣 *Эффект активирован!* Следующая задача: +75 за успех, -50 за ошибку!

💡 Артефакт добавлен в инвентарь!
```

---

### `handle_alchemy_callback(update, context)` 🎯
Обработчик нажатий на inline-кнопки алхимии.

**Поддерживаемые `callback_data`:**
| Значение | Действие |
|----------|----------|
| `"back_to_game"` | Вернуться в игру (редактирование сообщения) |
| `"craft_{item_id}"` | Создать артефакт через `execute_craft()` |

**Алгоритм для `craft_`:**
```
1. Извлечь item_id из callback_data
2. Проверить существование предмета
3. Вызвать execute_craft() (с await!)
4. Если успех:
   ├─ Получить сообщение активации через get_alchemy_activation_message()
   ├─ Если замок открыт → отправить комментарий Владимира через send_character_message_by_id()
   └─ Иначе → отредактировать сообщение с активацией
5. Если ошибка → показать сообщение об ошибке
6. Обработать исключения при редактировании сообщения
```

> ⚠️ **Важно:** Для отправки сообщения с аватаркой в коллбэке используется `send_character_message_by_id()`, а не `send_character_message()`, так как в коллбэке нет объекта `update.message`.

---

## ⚠️ Важные замечания

### 1. Асинхронность `spend_score`
Метод `score_manager.spend_score()` — **синхронный**, не требует `await`:
```python
# ✅ Правильно:
success, message = score_manager.spend_score(...)

# ❌ Ошибка:
success, message = await score_manager.spend_score(...)  # TypeError!
```

### 2. Типы артефактов и их поведение
| Тип | Хранение | Эффект | Пример |
|-----|----------|--------|--------|
| `one_time_risk` | Добавляется в `inventory[]` | Срабатывает на следующей задаче | Зелье Смелости |
| `level_wide_risk` | Добавляется в `inventory[]` | Действует до конца уровня | Инверсия счёта |
| `permanent` | Не добавляется в inventory | Постоянный бонус | (пока нет в рецептах) |

### 3. Проверка дубликатов
Для `one_time_risk` и `level_wide_risk` артефактов:
```python
if item_id in inventory:
    return False, "❌ Артефакт уже создан!"
```
Это предотвращает создание нескольких копий одноразовых эффектов.

### 4. Интеграция с Владимиром
Комментарии персонажа отправляются **только** если:
```python
if phrase_manager.is_castle_unlocked(progress):
    # Отправить фразу Владимира
```
Если замок закрыт — показывается только стандартное сообщение.

### 5. Обработка ошибок редактирования
При редактировании сообщений в коллбэках возможны ошибки («сообщение не изменено»):
```python
try:
    await query.edit_message_text(...)
except Exception as e:
    logger.warning(f"⚠️ Не удалось отредактировать сообщение: {e}")
```
Это нормальная ситуация, если пользователь быстро нажимает кнопки.

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py
     │
     ▼
universal_callback.py
     │ (callback_data: "craft_*")
     ▼
alchemy.handle_alchemy_callback()
     │
     ▼
execute_craft()
     │
┌────┴────┬────────────┐
▼         ▼            ▼
storage   score_    items.py
(save)    manager   (SHOP_ITEMS)
          (spend)
```

---

## 🧪 Примеры использования

```python
# 1. Проверка доступных рецептов
progress = {"unlocked_zones": ["addition", "subtraction"], "completed_normal_game": False}
available = get_available_recipes(progress)
# → ["bravery_potion"]

# 2. Создание артефакта программно
success, msg = await execute_craft(
    user_id=123456,
    item_id="bravery_potion",
    storage=player_storage,
    score_manager=score_mgr
)
if success:
    print(f"✅ {msg}")
else:
    print(f"❌ {msg}")

# 3. Получение сообщения активации
activation = get_alchemy_activation_message("bravery_potion")
# → "✨ Ты создала **Зелье Смелости**! ... +75 за успех, -50 за ошибку!"

# 4. Генерация клавиатуры
keyboard = get_alchemy_inline_keyboard(
    available_items=["bravery_potion"],
    current_balance=200
)
# → InlineKeyboardMarkup с кнопками "✅ Создать Зелье Смелости (150)" и "⬅️ Назад"
```

---

## 🛠 Чеклист при добавлении нового рецепта

1. [ ] Добавить запись в `ALCHEMY_RECIPES` с уникальным `item_id`
2. [ ] Указать `cost_in_score` и `unlocks_after`
3. [ ] Добавить предмет в `SHOP_ITEMS` (в `items.py`) с полями:
   - `name`, `description`, `type`, `effect`, `cost_in_score`
   - Для `one_time_risk`: `success_bonus`, `failure_penalty`
   - Для `level_wide_risk`: `error_reward`, `correct_reward`, `cancel_cost`
4. [ ] Обновить `get_alchemy_activation_message()` если добавлен новый `effect`
5. [ ] Протестировать: разблокировка, создание, активация эффекта
6. [ ] Добавить фразу для Владимира в `vladimir_phrases.json` (опционально)

---

*Документация актуальна для версии 3.2. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/HANDLERS_ALCHEMY.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/HANDLERS_ALCHEMY.md
   git commit -m "docs: add alchemy handler documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `handlers/narrative_manager.py` — управление фразами персонажей, отправка сообщений с аватарками
2. `database/storage.py` — работа с БД: пользователи, прогресс, логирование
3. `core/vladimir_persona.py` — логика персонажа Владимира, диалоги, настроения

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.