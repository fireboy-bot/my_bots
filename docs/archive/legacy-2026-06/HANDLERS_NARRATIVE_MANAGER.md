[#021]
Привет. Файл `handlers/narrative_manager.py` получил. Это модуль управления нарративом: фразы персонажей, аватарки, контекстные сообщения и интеграция с кэшем изображений.

Ниже — готовая документация. Просто сохрани в `docs/HANDLERS_NARRATIVE_MANAGER.md`.

---

## 📄 Файл: `docs/HANDLERS_NARRATIVE_MANAGER.md`

```markdown
# 🎭 Narrative Manager — Управление фразами и аватарками персонажей

> **Файл:** `handlers/narrative_manager.py`  
> **Версия:** 3.4 (Fix: user_data: Dict + context.bot_data) 🎩🫖✅  
> **Ответственность:** Фразы персонажей, отправка сообщений с аватарками, управление контекстом диалогов

---

## 📋 Обзор

`narrative_manager.py` — модуль, отвечающий за нарративную составляющую «Числяндии». Он обеспечивает:

| Функция | Описание |
|---------|----------|
| 🗣️ Фразы персонажей | Загрузка и выбор случайных реплик из JSON-файлов |
| 🖼️ Аватарки | Отправка сообщений с изображениями персонажей (кэш + локальные файлы) |
| 🎭 Настроения | Поддержка разных «настроений» персонажей (пока все → calm для Владимира) |
| 🔐 Доступ к контенту | Проверка разблокировки замка и уровней доступа |
| 📤 Гибкая отправка | Работа через адаптер + fallback на текст при ошибках |

```
┌─────────────────────┐
│  Narrative Manager  │
├─────────────────────┤
│ • PhraseManager     │ ← Фразы, контексты
│ • send_character_...│ ← Отправка с аватаркой
│ • CHARACTERS        │ ← Конфигурация персонажей
│ • VLADIMIR_MOODS    │ ← Настроения Владимира
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
avatar_   adapter
cache     (Telegram/VK)
```

---

## ⚙️ Конфигурация персонажей (`CHARACTERS`)

Словарь с параметрами всех персонажей бота.

```python
CHARACTERS = {
    "manunya": {
        "name": "Манюня",
        "avatar": "manunya.jpg",      # Имя файла аватарки
        "role": "guide"               # Роль в игре
    },
    "georgy": {
        "name": "Георгий",
        "avatar": "georgy.jpg",
        "role": "friend"
    },
    "vladimir": {
        "name": "Владимир",
        "avatar": None,               # Особая логика через VLADIMIR_MOODS
        "role": "butler"
    },
    "shop_keeper": {
        "name": "Торговец",
        "avatar": "shop_keeper.jpg",
        "role": "merchant"
    },
    "alchemist": {
        "name": "Алхимик",
        "avatar": "alchemist_mad.jpg",
        "role": "alchemist"
    }
}
```

**Поля конфигурации:**
| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `name` | `str` | Отображаемое имя персонажа | `"Владимир"` |
| `avatar` | `str \| None` | Имя файла аватарки в `images/` | `"vladimir_calm.jpg"` |
| `role` | `str` | Роль в игровом мире | `"butler"`, `"merchant"` |

---

## 🎭 Настроения Владимира (`VLADIMIR_MOODS`)

Словарь для выбора аватарки Владимира в зависимости от «настроения».

```python
VLADIMIR_MOODS = {
    "calm": "vladimir_calm.jpg",
    "approve": "vladimir_calm.jpg",      # ⚠️ Временно все → calm
    "disappointed": "vladimir_calm.jpg",
    "proud": "vladimir_calm.jpg",
    "thinking": "vladimir_calm.jpg",
    "relaxed": "vladimir_calm.jpg",
}
```

> ⚠️ **Важно:** Сейчас все настроения используют одну аватарку (`vladimir_calm.jpg`). Это временное решение — при добавлении новых изображений обновите словарь.

---

## 🗣️ Класс `PhraseManager`

Управление фразами персонажей (в первую очередь — Владимира).

### Инициализация

```python
phrase_manager = PhraseManager(phrases_path: str = "data/vladimir_phrases.json")
```

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `phrases_path` | `str` | `"data/vladimir_phrases.json"` | Путь к JSON-файлу с фразами |

**Что происходит при инициализации:**
1. Проверяется существование файла фраз
2. Загружается JSON в `self.vladimir_phrases`
3. При ошибке — логгируется предупреждение, используется пустой словарь

### Методы

#### `get_vladimir_phrase(context: str, **kwargs) -> str` 🎯
Возвращает случайную фразу Владимира для указанного контекста.

**Параметры:**
| Параметр | Тип | Описание | Пример |
|----------|-----|----------|--------|
| `context` | `str` | Ключ контекста в JSON | `"purchase_decoration"`, `"task_correct"` |
| `**kwargs` | `dict` | Переменные для форматирования фразы | `name="Артефакт Удачи"`, `level=3` |

**Алгоритм:**
```
1. Получить список фраз: self.vladimir_phrases.get(context, [])
2. Если список пуст → вернуть фразу по умолчанию: «Я к Вашим услугам, сударыня.»
3. Выбрать случайную фразу: random.choice(phrases)
4. Если есть kwargs → отформатировать: phrase.format(**kwargs)
5. Вернуть фразу
```

**Пример JSON (`vladimir_phrases.json`):**
```json
{
  "vladimir": {
    "purchase_decoration": [
      "«Превосходный выбор, сударыня. {name} украсит ваш замок.»",
      "«{name}? Отлично. Я уже приготовил для него почётное место.»"
    ],
    "task_correct": [
      "«Блестяще, сударыня! Логика — ваше второе имя.»",
      "«Именно так! Числа подчиняются вам.»"
    ]
  }
}
```

**Пример использования:**
```python
phrase = phrase_manager.get_vladimir_phrase(
    "purchase_decoration",
    name="Фонтан Мудрости"
)
# → «Превосходный выбор, сударыня. Фонтан Мудрости украсит ваш замок.»
```

---

#### `is_castle_unlocked(user_data: Dict) -> bool`
Проверяет, разблокирован ли замок для игрока.

**Условия разблокировки:**
```
✅ "final_boss" в defeated_bosses
✅ completed_normal_game == True
```

**Пример:**
```python
if phrase_manager.is_castle_unlocked(user_data):
    # Показать комментарии Владимира
```

---

#### `get_castle_access_level(user_data: Dict) -> str`
Возвращает уровень доступа к контенту замка.

**Возвращаемые значения:**
| Значение | Условие |
|----------|---------|
| `"full"` | Замок разблокирован (`is_castle_unlocked == True`) |
| `"preview"` | Уровень игрока ≥ 5, но замок ещё закрыт |
| `"locked"` | Уровень < 5 и замок закрыт |

---

## 📤 Функция `send_character_message` 🎯

Отправляет сообщение от имени персонажа с аватаркой (для обычных обновлений).

**Сигнатура:**
```python
async def send_character_message(
    update,
    context,
    character: str,
    text: str,
    mood: str = "calm",
    parse_mode: str = "HTML"
)
```

**Параметры:**
| Параметр | Тип | Описание | Пример |
|----------|-----|----------|--------|
| `update` | `Update` | Объект обновления от Telegram API | `update` из хендлера |
| `context` | `ContextTypes.DEFAULT_TYPE` | Контекст выполнения | `context` из хендлера |
| `character` | `str` | ID персонажа из `CHARACTERS` | `"vladimir"`, `"shop_keeper"` |
| `text` | `str` | Текст сообщения (подпись к фото) | `"✅ Покупка успешна!"` |
| `mood` | `str` | Настроение персонажа (для Владимира) | `"approve"`, `"thinking"` |
| `parse_mode` | `str` | Режим парсинга текста | `"HTML"`, `"Markdown"` |

**Алгоритм отправки:**
```
1. Получить adapter из context.bot_data
2. Получить avatar_cache из core.avatar_cache
3. Определить имя аватарки:
   ├─ Если character == "vladimir" → VLADIMIR_MOODS[mood]
   └─ Иначе → CHARACTERS[character]["avatar"]
4. Попробовать отправить из кэша:
   ├─ cache_key = avatar_name.replace(".jpg", "")
   ├─ file_id = avatar_cache.get_avatar(cache_key)
   └─ Если file_id найден → reply_photo(photo=file_id, ...)
5. Если кэш не сработал → попробовать локальный файл:
   ├─ Проверить images/{avatar_name}
   └─ Если файл есть → reply_photo(photo=InputFile(...), ...)
6. Если всё не сработало → fallback на reply_text(text, ...)
```

**Логирование:**
Все шаги логируются через `logger.info()` / `logger.warning()` для отладки.

**Пример использования:**
```python
await send_character_message(
    update, context, "vladimir",
    "🎩 «Превосходно, сударыня. Артефакт активирован.»",
    mood="approve"
)
```

---

## 📤 Функция `send_character_message_by_id`

Отправляет сообщение от персонажа по `user_id` (для кат-сцен и коллбэков).

**Сигнатура:**
```python
async def send_character_message_by_id(
    user_id: str, 
    text: str, 
    character: str, 
    mood: str, 
    context
)
```

**Отличия от `send_character_message`:**
| Аспект | `send_character_message` | `send_character_message_by_id` |
|--------|-------------------------|-------------------------------|
| Источник `update` | Использует `update.message` | Не требует `update`, только `user_id` |
| Метод отправки | `update.message.reply_photo()` | `adapter.bot.send_photo()` |
| Использование | Обычные хендлеры | Коллбэки, кат-сцены, фоновые события |

**Алгоритм:** Аналогичен `send_character_message`, но:
- Использует `adapter.bot.send_photo(chat_id=user_id, ...)` вместо `reply_photo`
- Fallback на `adapter.send_message(user_id=user_id, text=text, ...)`

**Пример использования (в коллбэке):**
```python
# Внутри handle_alchemy_callback
await send_character_message_by_id(
    user_id=str(update.effective_user.id),
    text=f"🎩 «{phrase}»\n\n✅ Артефакт активирован!",
    character="vladimir",
    mood="approve",
    context=context
)
```

---

## ⚠️ Важные замечания

### 1. Аватарки Владимира
Сейчас все настроения используют одну аватарку:
```python
# Временно:
VLADIMIR_MOODS = {
    "calm": "vladimir_calm.jpg",
    "approve": "vladimir_calm.jpg",  # ← То же самое
    # ...
}
```
**Рекомендация:** При добавлении новых изображений (`vladimir_approve.jpg`, `vladimir_thinking.jpg`) обновите словарь.

### 2. Путь к аватаркам
Аватарки ищутся в папке `images/` относительно корня проекта:
```
project_root/
├── images/
│   ├── vladimir_calm.jpg
│   ├── shop_keeper.jpg
│   └── ...
└── handlers/narrative_manager.py
```

### 3. Адаптер из `context.bot_data`
Функции получают адаптер через:
```python
adapter = context.bot_data.get('adapter')
```
Это обеспечивает совместимость с мульти-платформенной архитектурой (Telegram + VK/MAX).

### 4. Fallback на текст
Если аватарка не найдена (ни в кэше, ни локально), сообщение отправляется как текст:
```python
await update.message.reply_text(text, parse_mode=parse_mode)
```
Это предотвращает падение бота при проблемах с изображениями.

### 5. Форматирование фраз
Фразы в `vladimir_phrases.json` поддерживают форматирование через `.format()`:
```json
"«Артефакт {name} улучшен до уровня {level}!»"
```
Передавайте переменные через `**kwargs`:
```python
phrase_manager.get_vladimir_phrase("artifact_upgraded", name="Удача", level=3)
```

### 6. Логирование
Все важные шаги логируются:
```
🎬 send_character_message ВЫЗВАН: character=vladimir, mood=approve...
✅ Adapter получен из context.bot_data
🖼️ Avatar name: vladimir_calm.jpg
🔍 Cache lookup: key=vladimir_calm, file_id=✅
📤 Отправка фото из кэша: vladimir_calm
✅ Фото отправлено из кэша: vladimir_calm
```
Проверяйте `logs/app.log` при отладке отправки аватарок.

---

## 🔗 Интеграция с другими модулями

```
handlers/
├── alchemy.py          ──► send_character_message_by_id()
├── shop.py             ──► send_character_message()
├── castle.py           ──► PhraseManager.is_castle_unlocked()
└── narrative_manager.py
         │
         ▼
core/avatar_cache.py    ← Кэш аватарок (file_id)
platforms/adapter.py    ← Адаптер отправки (Telegram/VK)
data/vladimir_phrases.json ← Фразы персонажей
images/                 ← Файлы аватарок
```

---

## 🧪 Примеры использования

```python
# 1. Инициализация PhraseManager
phrase_manager = PhraseManager()

# 2. Получение фразы с форматированием
phrase = phrase_manager.get_vladimir_phrase(
    "artifact_upgraded",
    name="Артефакт Удачи",
    level=3
)

# 3. Проверка доступа к замку
if phrase_manager.is_castle_unlocked(user_data):
    # Показать премиум-контент
    pass

# 4. Отправка сообщения с аватаркой (в хендлере)
await send_character_message(
    update, context, "shop_keeper",
    "🛒 «Добро пожаловать! Что изволите?»",
    mood="calm"
)

# 5. Отправка по user_id (в коллбэке)
await send_character_message_by_id(
    user_id="123456",
    text="🎩 «Кат-сцена: Владимир появляется...»",
    character="vladimir",
    mood="proud",
    context=context
)

# 6. Получение уровня доступа
access = phrase_manager.get_castle_access_level(user_data)
if access == "preview":
    await update.message.reply_text("🔒 Замок откроется после победы над Финальным Владыкой!")
```

---

## 🛠 Чеклист при добавлении нового персонажа

1. [ ] Добавить запись в `CHARACTERS` с уникальным `id`, `name`, `avatar`, `role`
2. [ ] Добавить файл аватарки в папку `images/` (формат: `.jpg`, имя совпадает с `avatar` в конфиге)
3. [ ] Если персонаж — Владимир, добавить настроение в `VLADIMIR_MOODS` и соответствующий файл аватарки
4. [ ] Добавить фразы в `data/vladimir_phrases.json` (или создать новый файл для другого персонажа)
5. [ ] Протестировать отправку: `send_character_message(..., character="new_char", ...)`
6. [ ] Проверить fallback: удалить аватарку → убедиться, что сообщение отправляется как текст
7. [ ] Добавить логирование при необходимости

---

## 🔄 Расширение: добавление новых персонажей

Чтобы добавить нового персонажа (например, `"wizard"`):

1. **Конфигурация:**
```python
CHARACTERS["wizard"] = {
    "name": "Волшебник",
    "avatar": "wizard.jpg",
    "role": "mentor"
}
```

2. **Файл аватарки:**
```
images/wizard.jpg  ← добавить файл
```

3. **Фразы (опционально):**
```json
// data/vladimir_phrases.json (или новый файл)
{
  "wizard": {
    "greeting": ["«Магия чисел откроется тебе, дитя...»"],
    "spell_cast": ["«Заклинание сработало! +{bonus} очков!»"]
  }
}
```

4. **Использование:**
```python
await send_character_message(
    update, context, "wizard",
    phrase_manager.get_vladimir_phrase("greeting"),
    mood="calm"
)
```

---

*Документация актуальна для версии 3.4. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/HANDLERS_NARRATIVE_MANAGER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/HANDLERS_NARRATIVE_MANAGER.md
   git commit -m "docs: add narrative manager documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `database/storage.py` — работа с БД: пользователи, прогресс, логирование
2. `core/avatar_cache.py` — кэширование аватарок, загрузка из Telegram API
3. `core/vladimir_persona.py` — логика персонажа Владимира, диалоги, настроения

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.