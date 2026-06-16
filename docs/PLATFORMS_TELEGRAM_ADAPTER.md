[#027]
Привет. Файл `platforms/telegram_adapter.py` получил. Это адаптер для Telegram, который оборачивает Telegram Bot API в универсальный интерфейс `MessageAdapter`.

Ниже — готовая документация. Просто сохрани в `docs/PLATFORMS_TELEGRAM_ADAPTER.md`.

---

## 📄 Файл: `docs/PLATFORMS_TELEGRAM_ADAPTER.md`

```markdown
# 🤖 Telegram Adapter — Адаптер платформы Telegram

> **Файл:** `platforms/telegram_adapter.py`  
> **Версия:** 1.1 (Fix: parse_callback_data + isdigit safety) 🤖✅  
> **Ответственность:** Реализация интерфейса `MessageAdapter` для отправки сообщений через Telegram Bot API

---

## 📋 Обзор

`TelegramAdapter` — класс, который обеспечивает единый способ отправки сообщений в Telegram, абстрагируя специфику `python-telegram-bot` от бизнес-логики бота.

**Ключевые особенности:**
| Фича | Описание |
|------|----------|
| 🔀 Универсальный интерфейс | Реализует абстрактный класс `MessageAdapter` из `base_adapter.py` |
| 🖼️ Поддержка медиа | Отправка текста, фото с подписью, клавиатур |
| 🔢 Безопасная обработка ID | Конвертация `user_id` с защитой от `isdigit()` на не-строках |
| 🔄 Редактирование сообщений | Метод `edit_message()` для обновления существующих сообщений |
| 📦 Парсинг callback_data | Утилита `parse_callback_data()` для разбора данных кнопок |

```
┌─────────────────┐
│ TelegramAdapter │
├─────────────────┤
│ • send_message()│ ← Отправка текста/фото
│ • edit_message()│ ← Редактирование
│ • parse_...()   │ ← Разбор callback_data
│ • normalize_...()│ ← Приведение ID к строке
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
telegram.Bot  MessageAdapter
(API)         (интерфейс)
```

---

## ⚙️ Инициализация

```python
adapter = TelegramAdapter(
    bot: telegram.Bot,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None
)
```

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `bot` | `telegram.Bot` | ✅ | Экземпляр бота из `python-telegram-bot` |
| `context` | `ContextTypes.DEFAULT_TYPE` | ❌ | Контекст обработчика (для доступа к `bot_data`) |

**Пример создания (в `manyunya_bot.py`):**
```python
from platforms.telegram_adapter import TelegramAdapter

# В post_init():
tg_adapter = TelegramAdapter(application.bot)
application.bot_data['adapters'].append(tg_adapter)
```

---

## 📤 Методы отправки сообщений

### `send_message(...) -> bool` 🎯
Основной метод отправки сообщений в Telegram.

**Сигнатура:**
```python
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
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `user_id` | `str` | — | ID чата (строка или число) |
| `text` | `str` | — | Текст сообщения |
| `reply_markup` | `Any` | `None` | Клавиатура: `ReplyKeyboardMarkup` или `InlineKeyboardMarkup` |
| `photo` | `str` | `None` | `file_id` или URL изображения для отправки фото |
| `parse_mode` | `str` | `"Markdown"` | Режим парсинга: `"Markdown"`, `"HTML"` или `"plain"` |

**Возвращает:** `bool` — `True` если отправлено успешно, `False` при ошибке.

**Логика работы:**
```
1. Конвертировать user_id в строку для безопасной проверки
2. Если user_id.isdigit() → конвертировать в int, иначе оставить как строку
3. Если передан photo:
   ├─ Вызвать bot.send_photo() с caption=text
   └─ Использовать show_caption_above_media=True
4. Иначе:
   ├─ Вызвать bot.send_message()
   └─ Использовать disable_web_page_preview=True
5. Если parse_mode == "plain" → передать None (отключить парсинг)
6. Логировать результат
7. Вернуть True/False
```

**Примеры использования:**

```python
# 1. Простой текст
await adapter.send_message(
    user_id="123456",
    text="✅ Задача решена верно! +50 очков"
)

# 2. Текст с клавиатурой
from telegram import ReplyKeyboardMarkup, KeyboardButton

keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("🎮 Играть"), KeyboardButton("🏰 Замок")]],
    resize_keyboard=True
)
await adapter.send_message(
    user_id="123456",
    text="🏰 Главное меню",
    reply_markup=keyboard
)

# 3. Фото с подписью
await adapter.send_message(
    user_id="123456",
    text="🎩 «Добро пожаловать в замок, сударыня.»",
    photo="AgACAgIAAxkBAAIC... (file_id)",
    parse_mode="Markdown"
)

# 4. Отправка без форматирования
await adapter.send_message(
    user_id="123456",
    text="Сырой текст: 2 + 2 = 4",
    parse_mode="plain"  # Отключает Markdown/HTML
)
```

---

### `edit_message(...) -> bool`
Редактирует существующее сообщение (для обновления интерфейса).

**Сигнатура:**
```python
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

**Пример (в коллбэке):**
```python
# Обновление текста кнопки после нажатия
success = await adapter.edit_message(
    chat_id=str(update.effective_chat.id),
    message_id=update.callback_query.message.message_id,
    text="✅ Покупка успешна!",
    reply_markup=None  # Убрать клавиатуру
)
```

> ⚠️ **Важно:** Редактирование возможно только для сообщений, отправленных ботом, и не позже 48 часов после отправки (ограничение Telegram API).

---

## 🔧 Вспомогательные методы

### `parse_callback_data(data: str) -> Dict[str, str]` 🎯
Разбирает строку `callback_data` в словарь параметров.

**Формат входных данных:**
```
"action:param1:value1|param2:value2"
```

**Примеры:**
| Вход | Выход |
|------|--------|
| `"buy_item:id:potion_health|qty:1"` | `{"action": "buy_item", "id": "potion_health", "qty": "1"}` |
| `"back_to_game"` | `{"action": "back_to_game"}` |
| `"craft_elixir:type:health|level:3"` | `{"action": "craft_elixir", "type": "health", "level": "3"}` |

**Алгоритм:**
```
1. Разбить строку по "|" → получить список частей
2. Для каждой части:
   ├─ Если содержит ":" → разбить на key:value через partition(":")
   └─ Добавить в результат: result[key.strip()] = value.strip()
3. Если результат пуст, но data не пуст → считать всю строку действием: result["action"] = data
4. Вернуть словарь
```

**Пример использования:**
```python
# В универсальном обработчике коллбэков:
data = adapter.parse_callback_data(update.callback_query.data)

if data.get("action") == "buy_item":
    item_id = data.get("id")
    qty = int(data.get("qty", 1))
    # ... логика покупки
```

---

### `normalize_user_id(raw_id: Any) -> str`
Приводит Telegram `user_id` к строковому формату для единообразия с другими платформами.

**Зачем это нужно:**
- Telegram API возвращает `user_id` как `int` (например, `5001966771`)
- Другие платформы (VK, MAX) могут использовать строки
- В БД все ID хранятся как строки для совместимости

**Пример:**
```python
# Telegram возвращает int
raw_id = 5001966771
normalized = adapter.normalize_user_id(raw_id)
# → "5001966771" (строка)

# Теперь можно использовать в БД:
user = storage.get_user(normalized)
```

> ⚠️ **Логирование:** Метод логирует входные данные для отладки:
> ```
> 🔍 normalize_user_id: raw=5001966771 (type=int) -> str=5001966771
> ```

---

### `platform_name` (property)
Возвращает название платформы.

```python
print(adapter.platform_name)  # → "telegram"
```

Используется для логирования и отладки в мульти-платформенном режиме.

---

### `close()`
Завершает работу адаптера (для Telegram — заглушка).

```python
await adapter.close()  # Просто логирует и возвращает
```

---

## ⚠️ Важные замечания

### 1. Безопасная проверка `isdigit()`
В методе `send_message()` используется паттерн:
```python
user_id_str = str(user_id)
chat_id = int(user_id_str) if user_id_str.isdigit() else user_id_str
```

**Почему так:**
- `user_id` может прийти как `int` или `str`
- Вызов `.isdigit()` на `int` вызовет `AttributeError`
- Конвертация в `str` заранее предотвращает эту ошибку

### 2. Обработка `parse_mode="plain"`
Если передан `parse_mode="plain"`, метод передаёт `None` в API Telegram:
```python
parse_mode=parse_mode if parse_mode != "plain" else None
```

Это позволяет отправлять «сырой» текст без форматирования (полезно для отображения кода или формул).

### 3. Ограничения Telegram API
| Ограничение | Значение | Как обработано |
|-------------|----------|---------------|
| Макс. длина сообщения | 4096 символов | Не проверяется — ответственность на вызывающем коде |
| Частота сообщений | ~30 сообщений/сек на бота | Не регулируется — использовать `rate_limiter.py` при необходимости |
| Редактирование | Только свои сообщения, ≤48 часов | Возвращает `False` при ошибке, логгирует исключение |
| Фото + подпись | Caption ≤1024 символов | Не проверяется — обрезать текст перед отправкой при необходимости |

### 4. Логирование
Все операции логируются на уровне `DEBUG` или `ERROR`:
```python
logger.debug(f"✅ TG: сообщение отправлено {user_id}")
logger.error(f"❌ TG send error: {e}", exc_info=True)
```

**Как включить отладку:**
```python
# В config.py или .env:
LOG_LEVEL=DEBUG
```

### 5. Типы клавиатур
Адаптер принимает любые объекты `reply_markup`, но рекомендуется использовать:
- `telegram.ReplyKeyboardMarkup` — для кнопок под сообщением
- `telegram.InlineKeyboardMarkup` — для кнопок внутри сообщения (коллбэки)

**Пример создания inline-клавиатуры:**
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Купить", callback_data="buy_item:id:potion")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_shop")]
])
await adapter.send_message(user_id, "Выберите действие", reply_markup=keyboard)
```

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py
     │
     ▼
TelegramAdapter (в bot_data['adapters'])
     │
┌────┴────┬────────────┐
▼         ▼            ▼
send_   edit_     parse_
message() message() callback_data()
     │         │            │
     ▼         ▼            ▼
telegram.Bot  handlers/  universal_
(API)        narrative_ callback.py
             manager.py
```

**Поток отправки сообщения с аватаркой:**
```
1. narrative_manager.py определяет персонажа и настроение
2. Получает file_id из avatar_cache
3. Вызывает adapter.send_message(user_id, text, photo=file_id)
4. TelegramAdapter вызывает bot.send_photo(...)
5. Telegram доставляет сообщение пользователю
```

---

## 🧪 Примеры использования

```python
# 1. Инициализация в post_init бота
from platforms.telegram_adapter import TelegramAdapter

async def post_init(application: Application):
    tg_adapter = TelegramAdapter(application.bot)
    application.bot_data['adapters'] = [tg_adapter]
    application.bot_data['adapter'] = tg_adapter  # Для обратной совместимости

# 2. Отправка сообщения через адаптер (в хендлере)
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("❌ Ошибка адаптера")
        return
    
    user_id = adapter.normalize_user_id(update.effective_user.id)
    await adapter.send_message(
        user_id=user_id,
        text="🏰 *Главное меню*\n\nВыберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# 3. Парсинг callback_data в универсальном обработчике
async def universal_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    data = adapter.parse_callback_data(update.callback_query.data)
    
    if data.get("action") == "craft_item":
        item_id = data.get("id")
        # ... логика крафта

# 4. Редактирование сообщения после действия
async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    chat_id = str(update.effective_chat.id)
    message_id = update.callback_query.message.message_id
    
    await adapter.edit_message(
        chat_id=chat_id,
        message_id=message_id,
        text="✅ Покупка успешна! +🧪 Зелье здоровья",
        reply_markup=None
    )
```

---

## 🛠 Чеклист при расширении адаптера

1. [ ] Если добавляете новый тип медиа (видео, аудио, документ):
   - Реализовать метод `send_media(...)` в `TelegramAdapter`
   - Добавить абстрактный метод в `MessageAdapter` (base_adapter.py)
   - Обновить документацию

2. [ ] Если меняете логику обработки `user_id`:
   - Протестировать с `int` и `str` входными данными
   - Проверить совместимость с `PlayerStorage.normalize_user_id()`

3. [ ] Если добавляете поддержку новых `parse_mode`:
   - Обновить валидацию в `send_message()`
   - Добавить примеры в документацию

4. [ ] При изменении формата `callback_data`:
   - Обновить `parse_callback_data()` или добавить новый метод
   - Проверить обратную совместимость со старыми кнопками

---

## 🔍 Отладка и мониторинг

**Включить детальное логирование:**
```python
# В .env или config.py:
LOG_LEVEL=DEBUG

# Или программно:
logging.getLogger("platforms.telegram_adapter").setLevel(logging.DEBUG)
```

**Примеры логов:**
```
✅ [DEBUG] platforms.telegram_adapter: TG: сообщение отправлено 5001966771
❌ [ERROR] platforms.telegram_adapter: TG send error: Chat not found
🔍 [INFO] platforms.telegram_adapter: normalize_user_id: raw=5001966771 (type=int) -> str=5001966771
```

**Проверка работы адаптера:**
```python
# В админ-команде или тесте:
async def test_adapter(adapter: TelegramAdapter, test_user_id: str):
    success = await adapter.send_message(
        user_id=test_user_id,
        text="🧪 Тестовое сообщение от адаптера",
        parse_mode="plain"
    )
    print(f"✅ Тест {'пройдён' if success else 'провален'}")
```

---

*Документация актуальна для версии 1.1. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/PLATFORMS_TELEGRAM_ADAPTER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/PLATFORMS_TELEGRAM_ADAPTER.md
   git commit -m "docs: add Telegram adapter documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `platforms/base_adapter.py` — абстрактный интерфейс `MessageAdapter` для всех платформ
2. `platforms/max_adapter.py` — адаптер для VK/MAX (если используется)
3. `core/rate_limiter.py` — ограничение частоты запросов, анти-спам

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.