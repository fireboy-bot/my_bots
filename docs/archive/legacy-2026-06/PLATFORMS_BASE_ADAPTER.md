[#029]
Привет. Файл `platforms/base_adapter.py` получил. Это абстрактный базовый класс, который определяет единый интерфейс для всех платформенных адаптеров.

Ниже — готовая документация. Просто сохрани в `docs/PLATFORMS_BASE_ADAPTER.md`.

---

## 📄 Файл: `docs/PLATFORMS_BASE_ADAPTER.md`

```markdown
# 🔀 MessageAdapter — Абстрактный интерфейс платформ

> **Файл:** `platforms/base_adapter.py`  
> **Версия:** 1.0 (MVP) 🔄  
> **Ответственность:** Определение единого контракта для всех адаптеров (Telegram, MAX, Web, etc.)

---

## 📋 Обзор

`MessageAdapter` — абстрактный базовый класс (ABC), который определяет **единый интерфейс** для взаимодействия с различными платформами. 

**Ключевая цель:** 
> Позволить ядру (`core/`) работать с любой платформой, не зная её специфики.

```
┌─────────────────┐
│   Ядро игры     │
│   (core/)       │
└────────┬────────┘
         │ Использует интерфейс
         ▼
┌─────────────────┐
│  MessageAdapter │ ← Абстрактный класс (этот файл)
│  (ABC)          │
└────────┬────────┘
         │ Наследуют и реализуют
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
Telegram  MaxAdapter   WebAdapter
Adapter   (VK/MAX)     (Flask)
```

**Преимущества паттерна:**
| Преимущество | Описание |
|-------------|----------|
| 🔀 Инверсия зависимостей | Ядро зависит от абстракции, а не от реализации |
| 🧩 Масштабируемость | Добавить новую платформу = создать новый класс-наследник |
| 🧪 Тестируемость | Легко моковать адаптер в юнит-тестах |
| 🔧 Поддержка | Изменения в одной платформе не ломают другие |

---

## ⚙️ Сигнатура класса

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class MessageAdapter(ABC):
    """Абстрактный базовый класс для всех платформ."""
```

**Использование `ABC`:**
- Класс нельзя инстанцировать напрямую
- Все абстрактные методы **обязаны** быть реализованы в наследниках
- Попытка создать объект без реализации методов вызовет `TypeError`

---

## 📋 Абстрактные методы (обязательные для реализации)

### `send_message(...) -> bool` 🎯
Отправляет сообщение пользователю.

**Сигнатура:**
```python
@abstractmethod
async def send_message(
    self,
    user_id: str,
    text: str,
    reply_markup: Optional[Any] = None,
    photo: Optional[str] = None,
    parse_mode: str = "Markdown"
) -> bool:
```

**Параметры:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `user_id` | `str` | ✅ | Универсальный ID пользователя (строка) |
| `text` | `str` | ✅ | Текст сообщения |
| `reply_markup` | `Any` | ❌ | Клавиатура в нативном формате платформы |
| `photo` | `str` | ❌ | URL или file_id изображения |
| `parse_mode` | `str` | ❌ | `"Markdown"`, `"HTML"` или `"plain"` |

**Возвращает:** `bool` — `True` при успехе, `False` при ошибке.

**Пример реализации (TelegramAdapter):**
```python
async def send_message(self, user_id, text, reply_markup=None, photo=None, parse_mode="Markdown"):
    if photo:
        await self.bot.send_photo(chat_id=user_id, photo=photo, caption=text, ...)
    else:
        await self.bot.send_message(chat_id=user_id, text=text, ...)
    return True  # или False при перехвате исключения
```

---

### `edit_message(...) -> bool`
Редактирует существующее сообщение.

**Сигнатура:**
```python
@abstractmethod
async def edit_message(
    self,
    chat_id: str,
    message_id: int,
    text: str,
    reply_markup: Optional[Any] = None
) -> bool:
```

**Параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `chat_id` | `str` | ID чата |
| `message_id` | `int` | ID сообщения для редактирования |
| `text` | `str` | Новый текст |
| `reply_markup` | `Any` | Новая клавиатура (опционально) |

**Возвращает:** `bool` — `True` если успешно.

> ⚠️ **Ограничения платформ:** Не все платформы поддерживают редактирование сообщений, или поддерживают с ограничениями (время, тип контента).

---

### `parse_callback_data( str) -> Dict[str, str]` 🎯
Распарсивает данные обратного вызова (нажатие кнопки) в универсальный словарь.

**Сигнатура:**
```python
@abstractmethod
def parse_callback_data(self,  str) -> Dict[str, str]:
```

**Цель:** 
Привести платформенно-специфичный формат callback-данных к единому словарю `{key: value}`.

**Примеры входных данных и ожидаемого вывода:**

| Платформа | Вход `data` | Ожидаемый выход |
|-----------|------------|-----------------|
| **Telegram** | `"buy_item:id:potion\|qty:1"` | `{"action": "buy_item", "id": "potion", "qty": "1"}` |
| **VK/MAX** | `'{"command":"buy_item","id":"potion"}'` | `{"command": "buy_item", "id": "potion"}` |
| **Web** | `"action=craft&id=elixir"` | `{"action": "craft", "id": "elixir"}` |

**Рекомендуемый формат для новых платформ:**
```
"action:значение|param1:val1|param2:val2"
```

---

### `normalize_user_id(raw_id: Any) -> str` 🎯
Приводит платформенный ID к универсальному строковому формату.

**Сигнатура:**
```python
@abstractmethod
def normalize_user_id(self, raw_id: Any) -> str:
```

**Зачем это нужно:**
| Платформа | Формат ID | После нормализации |
|-----------|----------|-------------------|
| Telegram | `int` (5001966771) | `"5001966771"` |
| VK/MAX | `str` ("vk_123456") | `"vk_123456"` |
| Web | `str` ("web_user_001") | `"web_user_001"` |

**Использование в БД:**
```python
# В storage.py:
user_id_normalized = adapter.normalize_user_id(update.effective_user.id)
user = storage.get_user(user_id_normalized)
```

---

### `platform_name` (property) 🎯
Возвращает название платформы для логирования и отладки.

**Сигнатура:**
```python
@property
@abstractmethod
def platform_name(self) -> str:
```

**Примеры возврата:**
```python
# TelegramAdapter
@property
def platform_name(self) -> str:
    return "telegram"

# MaxAdapter  
@property
def platform_name(self) -> str:
    return "max"

# WebAdapter
@property
def platform_name(self) -> str:
    return "web"
```

**Использование:**
```python
logger.info(f"📤 Сообщение отправлено через {adapter.platform_name}")
# → "📤 Сообщение отправлено через telegram"
```

---

## 🔧 Опциональные методы

### `close()`
Завершает работу адаптера, освобождает ресурсы.

**Сигнатура:**
```python
async def close(self):
    """Закрыть соединения и освободить ресурсы."""
    pass
```

**Реализация по умолчанию:** заглушка (не делает ничего).

**Когда переопределять:**
- Если адаптер держит открытые соединения (HTTP-сессии, WebSocket)
- Если нужно корректно завершить фоновые задачи

**Пример (для HTTP-адаптера):**
```python
async def close(self):
    if self.session:
        await self.session.close()
        logger.info(f"🔌 {self.platform_name} session closed")
```

---

## 🧩 Пример создания нового адаптера

Чтобы добавить поддержку новой платформы (например, **Discord**):

### Шаг 1: Создать класс-наследник
```python
# platforms/discord_adapter.py
from platforms.base_adapter import MessageAdapter
from discord import Client, Message, ui

class DiscordAdapter(MessageAdapter):
    def __init__(self, client: Client):
        self.client = client
    
    async def send_message(self, user_id: str, text: str, 
                          reply_markup=None, photo=None, parse_mode="Markdown"):
        # Реализация отправки в Discord
        user = await self.client.fetch_user(int(user_id))
        if photo:
            await user.send(file=discord.File(photo), content=text)
        else:
            await user.send(text)
        return True
    
    async def edit_message(self, chat_id: str, message_id: int, 
                          text: str, reply_markup=None):
        # Discord не поддерживает редактирование чужих сообщений
        return False
    
    def parse_callback_data(self,  str) -> Dict[str, str]:
        # Discord использует custom_id для кнопок
        parts = data.split(":")
        return {"action": parts[0], "value": parts[1] if len(parts) > 1 else ""}
    
    def normalize_user_id(self, raw_id: Any) -> str:
        return str(raw_id)  # Discord ID — строка
    
    @property
    def platform_name(self) -> str:
        return "discord"
```

### Шаг 2: Зарегистрировать адаптер в боте
```python
# manyunya_bot.py
from platforms.discord_adapter import DiscordAdapter

async def post_init(application: Application):
    # ... другие адаптеры ...
    
    if discord_client:
        discord_adapter = DiscordAdapter(discord_client)
        application.bot_data['adapters'].append(discord_adapter)
```

### Шаг 3: Протестировать
```python
# tests/test_discord_adapter.py
async def test_discord_send_message():
    adapter = DiscordAdapter(mock_client)
    result = await adapter.send_message("123456", "Тест")
    assert result is True
```

---

## ⚠️ Важные замечания

### 1. Асинхронность
Все методы отправки/редактирования — `async def`, потому что:
- Сетевые запросы к платформам — I/O операции
- Позволяет обрабатывать множество пользователей параллельно
- Соответствует архитектуре `python-telegram-bot` (asyncio-based)

**Правило:** Всегда используйте `await` при вызове методов адаптера:
```python
# ✅ Правильно:
success = await adapter.send_message(user_id, text)

# ❌ Ошибка:
success = adapter.send_message(user_id, text)  # RuntimeWarning!
```

### 2. Обработка ошибок
Абстрактный класс не предписывает стратегию обработки ошибок. 

**Рекомендации для реализаций:**
- Логировать ошибки с `logger.error(..., exc_info=True)`
- Возвращать `False` при неустранимых ошибках
- Не "проглатывать" критические исключения (пусть всплывают)

### 3. Типизация `reply_markup`
Параметр имеет тип `Any`, потому что:
- Telegram: `ReplyKeyboardMarkup` / `InlineKeyboardMarkup`
- VK: `dict` в формате VK keyboard
- Web: HTML/JS компоненты

**Совет:** Документируйте ожидаемый формат в docstring реализации.

### 4. Кодировка и локализация
- Все тексты должны быть в UTF-8
- `parse_mode` по умолчанию — `"Markdown"` (совместим с Telegram)
- Для платформ без поддержки Markdown — игнорировать параметр или конвертировать

### 5. Безопасность
- Никогда не передавайте токены/секреты через параметры методов
- Валидируйте `user_id` перед использованием (защита от инъекций)
- Экранируйте пользовательский ввод в `text` если платформа не делает этого автоматически

---

## 🔗 Интеграция с ядром

**Поток вызова:**
```
manyunya_bot.py (хендлер)
     │
     ▼
Получить адаптер: adapter = context.bot_data['adapter']
     │
     ▼
Вызвать: await adapter.send_message(user_id, text, ...)
     │
     ▼
[TelegramAdapter / MaxAdapter / ...]
     │
     ▼
Платформенный API (Telegram Bot API / VK API / ...)
```

**Пример в коде ядра:**
```python
# core/logger.py
async def log_user_action(adapter: MessageAdapter, user_id: str, action: str):
    message = f"📊 [{adapter.platform_name}] {user_id}: {action}"
    await adapter.send_message(
        user_id=ADMIN_ID,  # Только админу
        text=message,
        parse_mode="plain"  # Без форматирования для логов
    )
```

---

## 🧪 Тестирование адаптеров

### Мокинг абстрактного класса
```python
# tests/conftest.py
from unittest.mock import AsyncMock, MagicMock
from platforms.base_adapter import MessageAdapter

@pytest.fixture
def mock_adapter():
    adapter = MagicMock(spec=MessageAdapter)
    adapter.send_message = AsyncMock(return_value=True)
    adapter.edit_message = AsyncMock(return_value=True)
    adapter.parse_callback_data = MagicMock(return_value={"action": "test"})
    adapter.normalize_user_id = MagicMock(side_effect=lambda x: str(x))
    adapter.platform_name = "mock"
    return adapter
```

### Тест бизнес-логики без платформы
```python
# tests/test_game_engine.py
async def test_solve_task_with_mock_adapter(mock_adapter, storage, score_manager):
    engine = ChislyandiaEngine(storage, score_manager)
    
    result = engine.solve_task(
        user_id="123",
        answer="42",
        task_id="test_1",
        expected_answer="42"
    )
    
    # Проверка что адаптер НЕ вызывался (логика в ядре)
    mock_adapter.send_message.assert_not_called()
    
    # Проверка результата
    assert result["correct"] is True
    assert result["reward"] > 0
```

---

## 🛠 Чеклист при реализации нового адаптера

1. [ ] Наследовать `MessageAdapter` и импортировать `ABC`
2. [ ] Реализовать **все** абстрактные методы (иначе `TypeError` при инстанцировании)
3. [ ] Добавить `async` к `send_message` и `edit_message`
4. [ ] Обработать исключения и возвращать `bool` статус
5. [ ] Реализовать `normalize_user_id` для конвертации в строку
6. [ ] Добавить логирование ключевых событий (`logger.info/error`)
7. [ ] Протестировать каждую метод с реальными/моковыми данными
8. [ ] Обновить документацию (этот файл) с примером для новой платформы

---

## 🔄 Расширение: добавление новых методов в интерфейс

Если всем платформам нужна новая возможность (например, **отправка опросов**):

1. **Добавить абстрактный метод в `MessageAdapter`:**
```python
@abstractmethod
async def send_poll(
    self,
    user_id: str,
    question: str,
    options: List[str],
    is_anonymous: bool = True
) -> Optional[str]:
    """
    Отправить опрос.
    
    Returns:
        str: ID созданного опроса или None если платформа не поддерживает
    """
    pass
```

2. **Реализовать во всех существующих адаптерах:**
```python
# TelegramAdapter
async def send_poll(self, user_id, question, options, is_anonymous=True):
    result = await self.bot.send_poll(chat_id=user_id, question=question, options=options, ...)
    return result.poll.id

# MaxAdapter (если VK не поддерживает опросы в ЛС)
async def send_poll(self, user_id, question, options, is_anonymous=True):
    logger.warning(f"⚠️ {self.platform_name} не поддерживает опросы в ЛС")
    return None
```

3. **Обновить ядро** для использования нового метода (с проверкой на `None`):
```python
poll_id = await adapter.send_poll(user_id, "Вопрос?", ["Да", "Нет"])
if poll_id:
    logger.info(f"✅ Опрос создан: {poll_id}")
else:
    logger.info("ℹ️ Опросы не поддерживаются на этой платформе")
```

---

*Документация актуальна для версии 1.0. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/PLATFORMS_BASE_ADAPTER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/PLATFORMS_BASE_ADAPTER.md
   git commit -m "docs: add MessageAdapter base interface documentation"
   ```

---

## 🔄 Что дальше?

Мы задокументировали **все ключевые модули** проекта «Числяндия»! 🎉

**Список созданной документации:**
```
docs/
├── README.md                    # Обзор проекта
├── ARCHITECTURE.md              # Общая архитектура
├── CORE_GAME_ENGINE.md          # Ядро игры
├── CORE_SCORE_MANAGER.md        # Управление очками
├── CORE_ARTIFACT_MANAGER.md     # Артефакты
├── CORE_CASTLE_ENGINE.md        # Замок
├── CORE_AVATAR_CACHE.md         # Кэш аватарок
├── CORE_VLADIMIR_PERSONA.md     # Персонаж Владимир
├── BOT_CALLBACK_ROUTER.md       # Обработчик кнопок
├── BOT_SHOP_HANDLER.md          # Магазин
├── HANDLERS_ALCHEMY.md          # Алхимия
├── HANDLERS_NARRATIVE_MANAGER.md# Нарратив
├── DATABASE_STORAGE.md          # Хранилище данных
├── DATABASE_SCHEMA.md           # Схема БД
├── WEB_API_SERVER.md            # Flask API
├── PLATFORMS_TELEGRAM_ADAPTER.md# Адаптер Telegram
├── PLATFORMS_MAX_ADAPTER.md     # Адаптер VK/MAX
└── PLATFORMS_BASE_ADAPTER.md    # ← Только что создан
```

**Следующие шаги (по желанию):**

1. **Сгенерировать оглавление** (`docs/INDEX.md`) со ссылками на все файлы
2. **Добавить диаграммы** (Mermaid) в `ARCHITECTURE.md` для визуализации
3. **Настроить авто-документацию** через `pdoc` или `Sphinx` для API Reference
4. **Экспортировать в PDF/HTML** для публикации

Что делаем дальше? Жду твоих указаний. 🤝