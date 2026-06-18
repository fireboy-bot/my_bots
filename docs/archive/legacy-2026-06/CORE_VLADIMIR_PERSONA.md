[#024]
Привет. Файл `core/vladimir_persona.py` получил. Это модуль управления персонажем Владимира — дворецкого Числяндии: аватарки, фразы, настроения.

Ниже — готовая документация. Просто сохрани в `docs/CORE_VLADIMIR_PERSONA.md`.

---

## 📄 Файл: `docs/CORE_VLADIMIR_PERSONA.md`

```markdown
# 🎩 Vladimir Persona — Персонаж дворецкого

> **Файл:** `core/vladimir_persona.py`  
> **Версия:** 1.0 (Persona + Avatar Structure) 🎩🫖  
> **Ответственность:** Управление аватарками, фразами и поведением персонажа ВладимирИр

---

## 📋 Обзор

`vladimir_persona.py` — модуль, определяющий визуальное и текстовое представление персонажа Владимира. Обеспечивает:

| Функция | Описание |
|---------|----------|
| 🖼️ Аватарки по настроению | Выбор изображения в зависимости от контекста (`calm`, `approve`, `disappointed`, ...) |
| 🗣️ Базовые фразы | Заглушка для текстовых реплик (основные фразы хранятся в `vladimir_phrases.json`) |
| 🔀 Fallback-логика | Если файл аватарки не найден → возвращается основная (`calm`) |
| 📦 Экспорт | Чёткий `__all__` для контролируемого импорта |

```
┌─────────────────────┐
│ vladimir_persona.py │
├─────────────────────┤
│ • VLADIMIR_AVATARS  │ ← Словарь {mood: path}
│ • get_vladimir_...  │ ← Функции выбора
│ • VLADIMIR_BASE_... │ ← Заглушка фраз
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
narrative_  data/
manager.py  vladimir_
(использует) phrases.json
```

> ⚠️ **Важно:** Этот модуль — «скелет» персонажа. Основные фразы хранятся в `data/vladimir_phrases.json` и загружаются через `PhraseManager` в `narrative_manager.py`.

---

## 🖼️ Конфигурация аватарок (`VLADIMIR_AVATARS`)

Словарь `{mood: file_path}` определяет, какое изображение показывать в зависимости от «настроения» персонажа.

```python
VLADIMIR_AVATARS = {
    "calm": "images/vladimir_calm.jpg",           # ✅ Основная (нейтральное состояние)
    "approve": "images/vladimir_approve.jpg",     # 🔄 Одобрение (покупки, улучшения)
    "disappointed": "images/vladimir_disappointed.jpg",  # 🔄 Разочарование (ошибки)
    "proud": "images/vladimir_proud.jpg",         # 🔄 Гордость (победы, достижения)
    "thinking": "images/vladimir_thinking.jpg",   # 🔄 Размышление (подсказки, сложные задачи)
    "relaxed": "images/vladimir_relaxed.jpg",     # 🔄 Расслабленность (секретные диалоги, лор)
}
```

**Правила именования:**
| Поле | Формат | Пример |
|------|--------|--------|
| Ключ настроения | `snake_case`, латиница | `"approve"`, `"disappointed"` |
| Путь к файлу | Относительно корня проекта | `"images/vladimir_calm.jpg"` |
| Расширение | Только `.jpg` (для совместимости с Telegram API) | `"file.jpg"` |

**Fallback-логика:**
```python
def get_vladimir_avatar(mood: str = "calm") -> str:
    return VLADIMIR_AVATARS.get(mood, VLADIMIR_AVATARS["calm"])
```
Если запрошенное настроение не найдено → автоматически возвращается `"calm"`.

---

## 🗣️ Базовые фразы (`VLADIMIR_BASE_PHRASES`)

Словарь-заглушка для текстовых реплик. **Основной источник фраз — `data/vladimir_phrases.json`**.

```python
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
```

**Контексты (ключи словаря):**
| Контекст | Когда используется | Пример |
|----------|-------------------|--------|
| `"greeting"` | Первое появление, вход в замок | «Добро пожаловать...» |
| `"locked"` | Попытка доступа к закрытому контенту | «Замок закрыт...» |
| *(основные)* | *Загружаются из JSON* | *См. `vladimir_phrases.json`* |

> ⚠️ **Не добавляйте новые фразы сюда!** Для расширения используйте `data/vladimir_phrases.json` и `PhraseManager`.

---

## 🔧 Функции модуля

### `get_vladimir_avatar(mood: str = "calm") -> str` 🎯
Возвращает путь к файлу аватарки по настроению.

**Параметры:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `mood` | `str` | `"calm"` | Ключ настроения из `VLADIMIR_AVATARS` |

**Возвращает:**
- `str` — путь к файлу аватарки (например, `"images/vladimir_approve.jpg"`)
- Если `mood` не найден → путь к `"calm"`

**Пример использования:**
```python
# В narrative_manager.py:
avatar_path = get_vladimir_avatar("approve")
# → "images/vladimir_approve.jpg"

# Отправка с fallback:
if os.path.exists(avatar_path):
    await send_photo(avatar_path, caption=text)
else:
    await send_text(text)  # Fallback на текст
```

---

### `get_vladimir_phrase(context: str) -> str`
Возвращает случайную фразу по контексту из базового словаря.

**Параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `context` | `str` | Ключ контекста (`"greeting"`, `"locked"`, ...) |

**Возвращает:**
- `str` — случайная фраза из списка для данного контекста
- Если контекст не найден → фраза из `"greeting"`

**Пример:**
```python
phrase = get_vladimir_phrase("locked")
# → "🎩 «Я буду ждать... с чаем. И совком.»"
```

> ⚠️ **Для продакшена используйте `PhraseManager.get_vladimir_phrase()`** — он загружает фразы из JSON и поддерживает форматирование.

---

## 📦 Экспорт (`__all__`)

Модуль явно экспортирует только публичные объекты:

```python
__all__ = [
    "VLADIMIR_AVATARS",        # ← Словарь аватарок
    "get_vladimir_avatar",     # ← Функция выбора аватарки
    "get_vladimir_phrase",     # ← Функция выбора фразы (заглушка)
]
```

**Правильный импорт:**
```python
# ✅ Правильно:
from core.vladimir_persona import get_vladimir_avatar, VLADIMIR_AVATARS

# ❌ Не рекомендуется (импорт всего):
from core.vladimir_persona import *
```

---

## 🔗 Интеграция с другими модулями

```
narrative_manager.py
     │
     ▼
from core.vladimir_persona import get_vladimir_avatar
     │
     ▼
avatar_path = get_vladimir_avatar(mood)
     │
     ▼
Отправка через avatar_cache / adapter
     │
     ▼
data/vladimir_phrases.json  ← Основной источник фраз
     │
     ▼
PhraseManager (в narrative_manager.py)
```

**Полный поток отправки сообщения с Владимиром:**
```
1. narrative_manager.py определяет контекст и настроение
2. Вызывает get_vladimir_avatar(mood) → получает путь к файлу
3. Проверяет кэш аватарок через avatar_cache.get_avatar()
4. Если кэш есть → отправляет file_id, иначе → загружает файл
5. Для текста: PhraseManager.get_vladimir_phrase(context, **kwargs)
6. Отправляет сообщение через adapter.send_photo() или send_message()
```

---

## ⚠️ Важные замечания

### 1. Аватарки: требования к файлам
| Требование | Описание |
|------------|----------|
| Формат | Только `.jpg` (Telegram API оптимизирован под JPEG) |
| Размер | Рекомендуется ≤ 1024×1024 пикселей, файл ≤ 1–2 MB |
| Имя | Должно точно совпадать с ключом в `VLADIMIR_AVATARS` |
| Путь | Относительно корня проекта: `"images/vladimir_*.jpg"` |

**Проверка наличия файлов:**
```python
import os
for mood, path in VLADIMIR_AVATARS.items():
    if not os.path.exists(path):
        print(f"⚠️ Не найдена аватарка: {path}")
```

### 2. Фразы: где хранить?
| Место | Назначение | Пример |
|-------|-----------|--------|
| `vladimir_persona.py` | Заглушки, дефолты | `VLADIMIR_BASE_PHRASES` |
| `data/vladimir_phrases.json` | **Основной источник** | `{"purchase": ["фраза1", "фраза2"]}` |
| `PhraseManager` | Загрузка + форматирование | `.get_vladimir_phrase("purchase", name="Артефакт")` |

**Не дублируйте фразы!** Если фраза есть в JSON — не добавляйте её в `VLADIMIR_BASE_PHRASES`.

### 3. Расширение: добавление нового настроения
Чтобы добавить новое настроение (например, `"excited"`):

1. **Добавить аватарку:**
   - Подготовить файл `images/vladimir_excited.jpg`
   - Добавить запись в `VLADIMIR_AVATARS`:
     ```python
     "excited": "images/vladimir_excited.jpg",
     ```

2. **Добавить фразы (в JSON, не в py-файл!):**
   ```json
   // data/vladimir_phrases.json
   {
     "vladimir": {
       "excited": [
         "🎩 «Превосходно, сударыня! Это именно то, что нужно!»",
         "🎩 «Я в восторге от Вашего выбора!»"
       ]
     }
   }
   ```

3. **Использовать в коде:**
   ```python
   await send_character_message(
       update, context, "vladimir",
       phrase_manager.get_vladimir_phrase("excited"),
       mood="excited"  # ← ключ из VLADIMIR_AVATARS
   )
   ```

### 4. Локализация
Сейчас все фразы на русском. Для поддержки других языков:
- Создайте отдельные JSON-файлы: `vladimir_phrases_en.json`, `vladimir_phrases_kz.json`
- Модифицируйте `PhraseManager` для выбора файла по языку пользователя
- Аватарки остаются общими (визуал не зависит от языка)

---

## 🧪 Примеры использования

```python
# 1. Получение пути к аватарке
from core.vladimir_persona import get_vladimir_avatar

# Нейтральное состояние
path = get_vladimir_avatar("calm")
# → "images/vladimir_calm.jpg"

# Неизвестное настроение → fallback на calm
path = get_vladimir_avatar("unknown_mood")
# → "images/vladimir_calm.jpg"

# 2. Проверка наличия файла перед отправкой
import os
avatar_path = get_vladimir_avatar("approve")
if os.path.exists(avatar_path):
    # Можно отправлять
    await send_photo(avatar_path, caption="Текст")
else:
    # Fallback на текст
    await send_message("Текст")

# 3. Получение базовой фразы (только для тестов!)
from core.vladimir_persona import get_vladimir_phrase

phrase = get_vladimir_phrase("greeting")
# → "🎩 «Добро пожаловать в Ваш Замок, сударыня.»"

# 4. Продакшен-способ: через PhraseManager
from handlers.narrative_manager import PhraseManager

phrase_manager = PhraseManager()
phrase = phrase_manager.get_vladimir_phrase(
    "artifact_upgraded",
    name="Артефакт Удачи",
    level=3
)
# → "🎩 «{name} улучшен до уровня {level}! Превосходный выбор, сударыня.»"
```

---

## 🛠 Чеклист при добавлении нового контента

### Для аватарок:
1. [ ] Подготовить изображение в формате `.jpg`, размер ≤ 1024×1024, файл ≤ 2 MB
2. [ ] Сохранить в `images/` с именем `vladimir_<mood>.jpg`
3. [ ] Добавить запись в `VLADIMIR_AVATARS` с ключом `<mood>`
4. [ ] Проверить путь: `os.path.exists(VLADIMIR_AVATARS["<mood>"])`
5. [ ] Протестировать отправку через `narrative_manager.send_character_message()`

### Для фраз:
1. [ ] **Не редактировать** `VLADIMIR_BASE_PHRASES` (это заглушка!)
2. [ ] Открыть `data/vladimir_phrases.json`
3. [ ] Добавить новый контекст в секцию `"vladimir"`:
   ```json
   "new_context": ["фраза 1", "фраза 2 с {переменной}"]
   ```
4. [ ] Если фраза использует переменные → протестировать форматирование:
   ```python
   phrase_manager.get_vladimir_phrase("new_context", переменная="значение")
   ```
5. [ ] Добавить описание контекста в документацию (этот файл)

### Для нового настроения:
1. [ ] Выполнить чеклист для аватарок
2. [ ] Добавить фразы в JSON (чеклист для фраз)
3. [ ] Обновить таблицу «Контексты» в этой документации
4. [ ] Протестировать полный поток: выбор настроения → отправка → отображение

---

## 🔍 Отладка и мониторинг

**Проверка целостности конфигурации:**
```python
# В консоли или тесте:
from core.vladimir_persona import VLADIMIR_AVATARS
import os

print("🔍 Проверка аватарок Владимира:")
for mood, path in VLADIMIR_AVATARS.items():
    exists = "✅" if os.path.exists(path) else "❌"
    print(f"{exists} {mood:15} → {path}")
```

**Пример вывода:**
```
🔍 Проверка аватарок Владимира:
✅ calm            → images/vladimir_calm.jpg
❌ approve         → images/vladimir_approve.jpg  # ← Нужно добавить!
✅ disappointed    → images/vladimir_disappointed.jpg
...
```

**Логирование в production:**
```python
# В narrative_manager.py при отправке:
logger.debug(f"🎩 Владимир: mood={mood}, avatar={avatar_path}")
```

---

*Документация актуальна для версии 1.0. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/CORE_VLADIMIR_PERSONA.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/CORE_VLADIMIR_PERSONA.md
   git commit -m "docs: add Vladimir persona core module documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `web/api_server.py` — Flask API для веб-версии: эндпоинты, аутентификация, CORS
2. `platforms/telegram_adapter.py` — адаптер Telegram: отправка сообщений, обработка обновлений
3. `database/schema.py` — схема базы данных: таблицы, миграции, индексы

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.