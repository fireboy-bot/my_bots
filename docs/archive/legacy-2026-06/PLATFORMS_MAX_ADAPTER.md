[#028]
Привет. Файл `platforms/max_adapter.py` получил. Это адаптер для платформы MAX (VK Mini Apps / VK Мессенджер), который оборачивает VK API в универсальный интерфейс `MessageAdapter`.

Ниже — готовая документация. Просто сохрани в `docs/PLATFORMS_MAX_ADAPTER.md`.

---

## 📄 Файл: `docs/PLATFORMS_MAX_ADAPTER.md`

```markdown
# 🟣 Max Adapter — Адаптер платформы MAX (VK)

> **Файл:** `platforms/max_adapter.py`  
> **Версия:** 1.0 (MVP) 🟣  
> **Ответственность:** Реализация интерфейса `MessageAdapter` для отправки сообщений через VK API (VK Mini Apps / VK Мессенджер)

---

## 📋 Обзор

`MaxAdapter` — класс, который обеспечивает единый способ отправки сообщений в платформу MAX (VK), абстрагируя специфику VK API от бизнес-логики бота.

**Ключевые особенности:**
| Фича | Описание |
|------|----------|
| 🔀 Универсальный интерфейс | Реализует абстрактный класс `MessageAdapter` из `base_adapter.py` |
| 🔄 Конвертация клавиатур | Автоматическая конвертация `ReplyKeyboardMarkup`/`InlineKeyboardMarkup` → VK keyboard format |
| 🔢 Нормализация ID | Приведение `user_id` к формату `"vk_<число>"` для единообразия |
| 📦 Парсинг callback | Поддержка JSON payload и строкового формата от VK |
| 🌐 HTTP-запросы | Использование `requests` для взаимодействия с VK API |

```
┌─────────────────┐
│   MaxAdapter    │
├─────────────────┤
│ • send_message()│ ← Отправка текста/кнопок
│ • edit_message()│ ← Редактирование
│ • _convert_...()│ ← Конвертация клавиатур
│ • parse_...()   │ ← Разбор callback_data
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
VK API     MessageAdapter
(requests)  (интерфейс)
```

---

## ⚙️ Инициализация и конфигурация

### Конструктор

```python
adapter = MaxAdapter(config: Dict[str, Any])
```

**Параметры `config`:**
| Ключ | Тип | Обязательный | По умолчанию | Описание |
|------|-----|-------------|-------------|----------|
| `vk_token` | `str` | ✅ | — | Токен сообщества ВКонтакте (обязательно) |
| `vk_version` | `str` | ❌ | `"5.131"` | Версия VK API |
| `group_id` | `str/int` | ❌ | `None` | ID сообщества для отправки от имени группы |
| `api_url` | `str` | ❌ | `"https://api.vk.com/method"` | Базовый URL API (для кастомных эндпоинтов) |

**Пример создания:**
```python
from platforms.max_adapter import MaxAdapter

config = {
    'vk_token': os.getenv('VK_TOKEN'),
    'vk_version': '5.131',
    'group_id': os.getenv('VK_GROUP_ID'),
}
vk_adapter = MaxAdapter(config)
```

> ⚠️ **Важно:** Если `vk_token` не передан — конструктор выбросит `ValueError`.

---

## 📤 Методы отправки сообщений

### `send_message(...) -> bool` 🎯
Основной метод отправки сообщений в платформу MAX (VK).

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
| `user_id` | `str` | — | ID пользователя (`"vk_123456"` или `"123456"`) |
| `text` | `str` | — | Текст сообщения |
| `reply_markup` | `Any` | `None` | Клавиатура (Telegram format → конвертируется) |
| `photo` | `str` | `None` | URL изображения (пока добавляется как ссылка в тексте) |
| `parse_mode` | `str` | `"Markdown"` | Режим парсинга: `"HTML"`, `"Markdown"`, `"MarkdownV2"` |

**Возвращает:** `bool` — `True` если отправлено успешно, `False` при ошибке.

**Особенности реализации:**
1. **Извлечение VK ID:** `_extract_vk_id()` конвертирует `"vk_123456"` → `123456`
2. **Конвертация клавиатуры:** `_convert_keyboard()` преобразует формат Telegram → VK
3. **Обработка фото:** Пока поддерживается только добавление URL в текст (полная загрузка через `photos.getMessagesUploadServer` требует доработки)
4. **Запрос к API:** `_make_api_request()` делает POST-запрос к `messages.send`

**Пример использования:**
```python
# Простой текст
await adapter.send_message(
    user_id="vk_123456",
    text="✅ Задача решена верно! +50 очков"
)

# С клавиатурой
from telegram import ReplyKeyboardMarkup, KeyboardButton

keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("🎮 Играть"), KeyboardButton("🏰 Замок")]],
    resize_keyboard=True
)
await adapter.send_message(
    user_id="vk_123456",
    text="🏰 Главное меню",
    reply_markup=keyboard
)

# С изображением (упрощённо)
await adapter.send_message(
    user_id="vk_123456",
    text="🎩 «Добро пожаловать в замок, сударыня.»",
    photo="https://example.com/image.jpg"  # Будет добавлено как ссылка в текст
)
```

---

### `edit_message(...) -> bool`
Редактирует существующее сообщение в VK.

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
| `chat_id` | `str` | ID чата/пользователя |
| `message_id` | `int` | ID сообщения для редактирования |
| `text` | `str` | Новый текст |
| `reply_markup` | `Any` | Новая клавиатура (опционально) |

**Возвращает:** `bool` — `True` если успешно.

> ⚠️ **Ограничения VK API:**
> - Редактировать можно только сообщения, отправленные ботом
> - Доступно редактирование только в течение короткого времени после отправки
> - Метод использует `messages.edit` вместо `messages.send`

---

## 🔧 Вспомогательные методы

### `_convert_keyboard(keyboard_data: Any) -> Optional[Dict]` 🎯
Конвертирует клавиатуру из формата Telegram в формат VK API.

**Входные форматы:**
- `telegram.ReplyKeyboardMarkup`
- `telegram.InlineKeyboardMarkup`
- `list` строк кнопок
- Уже готовый `dict` в формате VK

**Выходной формат (VK keyboard):**
```json
{
  "one_time": false,
  "inline": false,
  "buttons": [
    [
      {
        "action": {
          "type": "text",
          "payload": "{\"command\":\"btn_Играть\"}",
          "label": "Играть"
        }
      }
    ]
  ]
}
```

**Особенности:**
- `payload` ограничивается 255 байтами (требование VK API)
- Если входные данные уже в формате VK — возвращаются как есть
- При ошибке конвертации возвращается `None` (клавиатура не добавляется)

**Пример конвертации:**
```python
# Вход: ReplyKeyboardMarkup с кнопкой "Играть"
# Выход:
{
  "one_time": False,
  "inline": False,
  "buttons": [[
    {
      "action": {
        "type": "text",
        "payload": "{\"command\":\"btn_Играть\"}",
        "label": "Играть"
      }
    }
  ]]
}
```

---

### `parse_callback_data( str) -> Dict[str, str]`
Распарсивает `callback_data` от VK.

**Поддерживаемые форматы входа:**
| Формат | Пример | Результат |
|--------|--------|-----------|
| JSON payload | `'{"command":"buy_item"}'` | `{"command": "buy_item"}` |
| Строка `key:value` | `"action:buy|id:potion"` | `{"action": "buy", "id": "potion"}` |
| Простая строка | `"back_to_game"` | `{"action": "back_to_game"}` |

**Алгоритм:**
```
1. Попытаться распарсить как JSON (VK payload)
2. Если не удалось → разбить по "|" и ":" как "key:value"
3. Если нет разделителей → считать всю строку значением "action"
4. Вернуть словарь
```

**Пример использования:**
```python
# В универсальном обработчике коллбэков:
data = adapter.parse_callback_data(callback_payload)

if data.get("command") == "buy_item":
    item_id = data.get("id")
    # ... логика покупки
```

---

### `normalize_user_id(raw_id: Any) -> str`
Приводит VK `user_id` к универсальному строковому формату.

**Поддерживаемые входные форматы:**
| Вход | Выход |
|------|--------|
| `123456` (int) | `"vk_123456"` |
| `"123456"` (str) | `"vk_123456"` |
| `"vk_123456"` | `"vk_123456"` (без изменений) |
| `"-123456"` (группа) | `"vk_-123456"` |

**Зачем это нужно:**
- Единое хранение ID в БД независимо от платформы
- Упрощение логики сравнения и поиска пользователей

**Пример:**
```python
raw_id = 123456  # от VK API
normalized = adapter.normalize_user_id(raw_id)
# → "vk_123456"

# Теперь можно использовать в БД:
user = storage.get_user(normalized)
```

---

### `platform_name` (property)
Возвращает название платформы.

```python
print(adapter.platform_name)  # → "max"
```

Используется для логирования и отладки в мульти-платформенном режиме.

---

### `close()`
Завершает работу адаптера (для `requests` — заглушка).

```python
await adapter.close()  # Просто логирует и возвращает
```

---

## 🔧 Внутренние методы

### `_make_api_request(method: str, params: Dict) -> Optional[Dict]`
Делает запрос к VK API.

**Алгоритм:**
```
1. Сформировать URL: {api_url}/{method}
2. Добавить access_token и version к параметрам
3. Отправить POST-запрос с таймаутом 10 секунд
4. Обработать ответ:
   ├─ Если есть 'error' → залогировать и вернуть None
   └─ Иначе → вернуть result['response']
5. Обработать исключения (timeout, network errors)
```

**Возвращает:** `dict` с ответом или `None` при ошибке.

**Логирование ошибок:**
```
❌ VK API error: 14 - ComService error
❌ VK API timeout: messages.send
❌ Ошибка запроса к VK API: Connection refused
```

---

### `_extract_vk_id(user_id: str) -> int`
Извлекает числовой VK ID из строки.

**Поддерживаемые форматы:**
| Вход | Выход |
|------|--------|
| `"123456"` | `123456` |
| `"vk_123456"` | `123456` |
| `"-123456"` (группа) | `-123456` |
| `123456` (int) | `123456` |

**Используется внутри:** `send_message()`, `edit_message()`, `normalize_user_id()`

---

## ⚠️ Важные замечания

### 1. Ограничения по фото
Текущая реализация **не поддерживает** полноценную загрузку фото в VK:
```python
# Упрощённая обработка:
if photo and photo.startswith('http'):
    params['message'] = f"{text}\n\n🖼️ {photo}"
```

**Для полноценной поддержки нужно:**
1. Вызвать `photos.getMessagesUploadServer`
2. Загрузить файл через полученный URL
3. Вызвать `photos.saveMessagesPhoto`
4. Использовать `attachment` параметр в `messages.send`

### 2. Формат клавиатур VK
VK API имеет строгие требования к клавиатурам:
| Требование | Значение |
|-----------|----------|
| Макс. кнопок в строке | 4 |
| Макс. строк | 10 |
| Макс. длина `label` | 40 символов |
| Макс. длина `payload` | 255 байт |

`_convert_keyboard()` автоматически обрезает `payload` до 255 байт, но не проверяет остальные ограничения.

### 3. Таймауты и обработка ошибок
Все запросы к VK API имеют таймаут 10 секунд:
```python
response = requests.post(url, data=params, timeout=10)
```

**Рекомендации:**
- Для продакшена настройте `retry` логику при сетевых ошибках
- Логируйте `error_code` из ответов VK для отладки

### 4. Токены и безопасность
- **Никогда не коммитьте** `vk_token` в репозиторий
- Храните токен в `.env`: `VK_TOKEN=your_token_here`
- Используйте `group_id` для отправки от имени сообщества (требует прав)

### 5. Редактирование сообщений
Метод `edit_message()` имеет ограничения со стороны VK:
- Можно редактировать только свои сообщения
- Доступно редактирование в течение ~24 часов после отправки
- Нельзя добавить/удалить вложения при редактировании

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py
     │
     ▼
MaxAdapter (в bot_data['adapters'])
     │
┌────┴────┬────────────┐
▼         ▼            ▼
send_   edit_     parse_
message() message() callback_data()
     │         │            │
     ▼         ▼            ▼
VK API    handlers/  universal_
(requests) narrative_ callback.py
          manager.py
```

**Поток отправки сообщения:**
```
1. narrative_manager.py определяет текст и персонажа
2. Вызывает adapter.send_message(user_id, text, ...)
3. MaxAdapter конвертирует keyboard и извлекает vk_id
4. Делает POST-запрос к https://api.vk.com/method/messages.send
5. VK доставляет сообщение пользователю в приложении
```

---

## 🧪 Примеры использования

```python
# 1. Инициализация в post_init бота
from platforms.max_adapter import MaxAdapter

async def post_init(application: Application):
    vk_config = {
        'vk_token': os.getenv('VK_TOKEN'),
        'vk_version': '5.131',
        'group_id': os.getenv('VK_GROUP_ID'),
    }
    vk_adapter = MaxAdapter(vk_config)
    application.bot_data['adapters'].append(vk_adapter)

# 2. Отправка сообщения через адаптер (в хендлере)
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    if not adapter or adapter.platform_name != 'max':
        return  # Этот хендлер для MAX
    
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
    if adapter.platform_name == 'max':
        # VK использует JSON payload
        data = adapter.parse_callback_data(update.callback_query.data)
        
        if data.get("command") == "craft_item":
            item_id = data.get("id")
            # ... логика крафта

# 4. Редактирование сообщения после действия
async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adapter = context.bot_data.get('adapter')
    if adapter.platform_name != 'max':
        return
    
    vk_id = adapter._extract_vk_id(str(update.effective_chat.id))
    
    success = await adapter.edit_message(
        chat_id=str(vk_id),
        message_id=update.callback_query.message.message_id,
        text="✅ Покупка успешна! +🧪 Зелье здоровья",
        reply_markup=None
    )
```

---

## 🛠 Чеклист при расширении адаптера

1. [ ] Если добавляете поддержку фото:
   - Реализовать загрузку через `photos.getMessagesUploadServer` → `photos.saveMessagesPhoto`
   - Добавить параметр `attachment` в `messages.send`
   - Протестировать с разными форматами изображений

2. [ ] Если меняете логику конвертации клавиатур:
   - Проверить ограничения VK: макс. 4 кнопки в строке, 10 строк
   - Убедиться, что `payload` ≤ 255 байт
   - Протестировать с `InlineKeyboardMarkup` и `ReplyKeyboardMarkup`

3. [ ] Если добавляете поддержку новых типов сообщений (опросы, стикеры):
   - Добавить метод `send_poll()`, `send_sticker()` и т.д.
   - Обновить абстрактный класс `MessageAdapter` если нужно
   - Добавить примеры в документацию

4. [ ] При изменении формата `callback_data`:
   - Обновить `parse_callback_data()` для поддержки нового формата
   - Проверить обратную совместимость со старыми кнопками
   - Протестировать парсинг JSON и строкового формата

---

## 🔍 Отладка и мониторинг

**Включить детальное логирование:**
```python
# В .env или config.py:
LOG_LEVEL=DEBUG

# Или программно:
logging.getLogger("platforms.max_adapter").setLevel(logging.DEBUG)
```

**Примеры логов:**
```
✅ [INFO] platforms.max_adapter: MaxAdapter инициализирован (VK API v5.131)
✅ [DEBUG] platforms.max_adapter: MAX: сообщение отправлено vk_123456
❌ [ERROR] platforms.max_adapter: VK API error: 14 - ComService error
❌ [ERROR] platforms.max_adapter: Не удалось извлечь VK ID из: invalid_id
```

**Проверка работы адаптера:**
```python
# В админ-команде или тесте:
async def test_max_adapter(adapter: MaxAdapter, test_user_id: str):
    success = await adapter.send_message(
        user_id=test_user_id,
        text="🧪 Тестовое сообщение от MAX адаптера",
        parse_mode="plain"
    )
    print(f"✅ Тест {'пройдён' if success else 'провален'}")
```

**Проверка токена:**
```python
# Простой запрос к API для проверки токена
result = adapter._make_api_request('groups.getById', {'group_id': adapter.group_id})
if result:
    print(f"✅ Токен валиден, группа: {result[0]['name']}")
else:
    print("❌ Токен невалиден или нет доступа к группе")
```

---

## 🔄 Расширение: добавление новых методов VK API

Чтобы добавить поддержку отправки опроса:

1. **Добавить метод в класс:**
```python
async def send_poll(
    self,
    user_id: str,
    question: str,
    options: List[str],
    is_anonymous: bool = True
) -> bool:
    vk_id = self._extract_vk_id(user_id)
    
    params = {
        'peer_id': vk_id,
        'question': question,
        'is_anonymous': is_anonymous,
        'add_answers': json.dumps(options, ensure_ascii=False)
    }
    
    result = self._make_api_request('messages.send', params)
    return result is not None
```

2. **Обновить абстрактный класс** `MessageAdapter` если метод должен быть унифицированным

3. **Протестировать** с разными вариантами опросов

4. **Обновить документацию** (этот файл)

---

*Документация актуальна для версии 1.0. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/PLATFORMS_MAX_ADAPTER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/PLATFORMS_MAX_ADAPTER.md
   git commit -m "docs: add MAX (VK) adapter documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `platforms/base_adapter.py` — абстрактный интерфейс `MessageAdapter` для всех платформ
2. `core/rate_limiter.py` — ограничение частоты запросов, анти-спам логика
3. `services/economy.py` — сервис управления экономикой игры

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.