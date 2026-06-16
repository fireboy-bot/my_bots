[#023]
Привет. Файл `core/avatar_cache.py` получил. Это модуль кэширования аватарок — критически важный компонент для отправки сообщений с изображениями персонажей через Telegram API.

Ниже — готовая документация. Просто сохрани в `docs/CORE_AVATAR_CACHE.md`.

---

## 📄 Файл: `docs/CORE_AVATAR_CACHE.md`

```markdown
# 🖼️ AvatarCache — Кэш аватарок персонажей

> **Файл:** `core/avatar_cache.py`  
> **Версия:** 2.0 (Vladimir Mood Avatars Support) 🗄️⚡🎩  
> **Ответственность:** Загрузка, кэширование и предоставление `file_id` аватарок для отправки через Telegram Bot API

---

## 📋 Обзор

`AvatarCache` — singleton-класс для управления кэшем аватарок персонажей. Решает проблему повторной загрузки изображений в Telegram API:

| Проблема | Решение |
|----------|---------|
| 🔄 Повторная загрузка одних и тех же файлов | Кэширование `file_id` в памяти и на диске |
| ⏱️ Долгая загрузка при старте бота | Инкрементальная загрузка с сохранением после каждого файла |
| 🗄️ Потеря кэша при перезапуске | Сохранение в `data/avatar_cache.json` |
| 🎭 Разные настроения персонажей | Поддержка нескольких аватарок на персонажа (Владимир: 6 настроений) |

```
┌─────────────────┐
│   AvatarCache   │
├─────────────────┤
│ • load_avatars()│ ← Загрузка из файлов → Telegram API
│ • get_avatar()  │ ← Получение file_id по ключу
│ • _save_to_file()│ ← Persist в JSON
│ • check_...()   │ ← Проверки готовности
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
Telegram   data/
Bot API   avatar_cache.json
(file_id)  (persist)
```

---

## ⚙️ Инициализация

### Глобальные функции

```python
# Инициализация (вызывается в post_init бота)
avatar_cache = init_avatar_cache(bot: Bot) -> AvatarCache

# Получение экземпляра в любом месте кода
cache = get_avatar_cache() -> Optional[AvatarCache]
```

### Конструктор класса

```python
cache = AvatarCache(bot: Bot)
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `bot` | `telegram.Bot` | Экземпляр бота для отправки фото в API |

**Что происходит при инициализации:**
1. Сохраняется ссылка на `bot`
2. Инициализируется пустой `_cache: Dict[str, str]`
3. Загружается словарь `avatar_paths` с путями к файлам
4. Флаг `_loading = False`

---

## 🗂️ Конфигурация аватарок (`avatar_paths`)

Словарь `{key: path}` определяет, какие файлы загружать и под какими ключами они будут доступны.

```python
self.avatar_paths = {
    # === ГЕРОИ ===
    "manunya": "images/manunya.jpg",
    "georgy": "images/georgy.jpg",
    
    # === ТОРГОВЕЦ И АЛХИМИК ===
    "shop_keeper": "images/shop_keeper.jpg",
    "alchemist_mad": "images/alchemist_mad.jpg",
    
    # === ВЛАДИМИР (6 настроений) ===
    "vladimir_calm": "images/vladimir_calm.jpg",
    "vladimir_approve": "images/vladimir_approve.jpg",
    "vladimir_disappointed": "images/vladimir_disappointed.jpg",
    "vladimir_proud": "images/vladimir_proud.jpg",
    "vladimir_thinking": "images/vladimir_thinking.jpg",
    "vladimir_relaxed": "images/vladimir_relaxed.jpg",
    
    # === БОССЫ ===
    "null_void": "images/null_void.jpg",
    "minus_shadow": "images/minus_shadow.jpg",
    "evil_multiplier": "images/evil_multiplier.jpg",
    "fracosaur": "images/fracosaur.jpg",
    "final_boss": "images/final_boss.jpg",
    
    # === ИСТИННЫЙ ВЛАДЫКА (3 фазы) ===
    "true_lord_calm": "images/true_lord_calm.jpg",
    "true_lord_angry": "images/true_lord_angry.jpg",
    "true_lord_desperate": "images/true_lord_desperate.jpg",
    
    # === ХРАНИТЕЛИ МИРОВ ===
    "time_keeper": "images/time_keeper.jpg",
    "measure_keeper": "images/measure_keeper.jpg",
    "logic_keeper": "images/logic_keeper.jpg",
}
```

**Правила именования:**
| Компонент | Формат | Пример |
|-----------|--------|--------|
| Ключ кэша | `snake_case` | `"vladimir_calm"` |
| Путь к файлу | Относительно `BASE_DIR` | `"images/vladimir_calm.jpg"` |
| Расширение | Только `.jpg` (Telegram API) | `"file.jpg"` |

> ⚠️ **Важно:** Ключи кэша используются в `narrative_manager.py` при вызове `avatar_cache.get_avatar(key)`.

---

## 🔄 Метод `load_avatars()` 🎯

Асинхронная загрузка всех аватарок в кэш Telegram.

**Сигнатура:**
```python
async def load_avatars(self) -> Dict[str, str]:
    """
    Returns:
        Dict[str, str]: {character_key: telegram_file_id}
    """
```

**Алгоритм:**
```
1. Если _loading=True → вернуть текущий кэш (защита от параллельных загрузок)
2. Установить _loading=True
3. Попытаться загрузить из файла: _load_from_file()
4. Если все аватарки уже в кэше → завершить
5. Иначе для каждой аватарки:
   ├─ Пропустить если уже загружена
   ├─ Проверить наличие файла на диске
   ├─ Отправить фото в admin_chat_id через bot.send_photo()
   ├─ Извлечь file_id из message.photo[-1].file_id
   ├─ Сохранить в _cache[character] = file_id
   ├─ ✅ Сохранить кэш на диск после КАЖДОЙ аватарки
   └─ await asyncio.sleep(0.1) для избежания лимитов
6. Установить _loading=False
7. Вернуть кэш
```

**Особенности реализации:**

### 🔐 Admin Chat ID
Для загрузки аватарок требуется `chat_id` администратора:
```python
admin_ids_str = os.getenv("ADMIN_IDS", "")
admin_chat_id = int(admin_ids_str.split(",")[0])  # Берём первого
```
> ⚠️ Убедитесь, что `ADMIN_IDS` задан в `.env` и бот имеет доступ к этому чату.

### 💾 Инкрементальное сохранение
```python
# После каждой успешной/неуспешной загрузки:
self._save_to_file()
```
Это предотвращает потерю прогресса при сбое в середине загрузки.

### ⏱️ Таймауты и обработка ошибок
```python
try:
    message = await asyncio.wait_for(
        self.bot.send_photo(...),
        timeout=10  # 10 секунд на отправку
    )
except asyncio.TimeoutError:
    self._cache[character] = None  # Помечаем как неудачу
```

---

## 💾 Персистентность кэша

### `_load_from_file() -> bool`
Загружает кэш из `data/avatar_cache.json`.

**Формат файла:**
```json
{
  "manunya": "AgACAgIAAxkBAAIC... (file_id)",
  "vladimir_calm": "AgACAgIAAxkBAAID...",
  "null_void": null
}
```

**Возвращает:** `True` если файл найден и загружен, `False` при ошибке.

### `_save_to_file()`
Сохраняет текущий кэш на диск.

**Особенности:**
- Создаёт папку `data/` если не существует
- Использует `ensure_ascii=False` для поддержки кириллицы в ключах
- `indent=2` для читаемости файла

---

## 🔍 Методы получения данных

### `get_avatar(character: str) -> Optional[str]` 🎯
Возвращает `file_id` для отправки в Telegram API.

```python
file_id = avatar_cache.get_avatar("vladimir_calm")
if file_id:
    await update.message.reply_photo(photo=file_id, caption="Текст")
```

**Возвращает:**
- `str` — `file_id` если аватарка загружена
- `None` если не найдена или не загружена

### `is_loaded(character: str) -> bool`
Проверяет, загружена ли конкретная аватарка.

```python
if avatar_cache.is_loaded("manunya"):
    # Можно безопасно использовать
    pass
```

### `is_loading() -> bool`
Проверяет, идёт ли процесс загрузки.

```python
if avatar_cache.is_loading():
    await update.message.reply_text("⏳ Аватарки загружаются...")
```

### `check_heroes_loaded() -> bool`
Специальная проверка: загружены ли Манюня и Георгий (критично для старта игры).

```python
if not avatar_cache.check_heroes_loaded():
    logger.warning("⚠️ Герои не загружены — игра может работать некорректно")
```

### `clear_cache()`
Очищает кэш в памяти и удаляет файл на диске.

> ⚠️ **Опасно:** Используйте только для отладки или принудительного обновления аватарок.

---

## ⚠️ Важные замечания

### 1. Лимиты Telegram Bot API
- **Rate Limits:** ~30 сообщений в секунду на бота
- **Размер файла:** Макс. 10 MB для фото
- **Формат:** Только JPG/PNG (конвертируйте если нужно)

**Как код избегает лимитов:**
```python
await asyncio.sleep(0.1)  # 100ms между загрузками
```

### 2. Требования к admin_chat_id
- Бот **должен быть добавлен** в чат администратора
- Администратор должен **разрешить боту отправлять сообщения**
- `ADMIN_IDS` в `.env` должен содержать валидный числовой ID

**Проверка:**
```bash
# Получить свой ID через @userinfobot или команду /myid в боте
```

### 3. Структура файлов
```
project_root/
├── core/avatar_cache.py
├── images/
│   ├── vladimir_calm.jpg      ← Должны существовать!
│   ├── manunya.jpg
│   └── ...
├── data/
│   └── avatar_cache.json      ← Создаётся автоматически
└── .env
    ADMIN_IDS=123456789        ← Обязательно для загрузки
```

### 4. Обработка отсутствующих файлов
Если файл не найден на диске:
```python
if not os.path.exists(full_path):
    self._cache[character] = None  # Помечаем как отсутствующий
    missing_count += 1
    continue  # Пропускаем, не прерывая загрузку остальных
```

### 5. Singleton-паттерн
Глобальная переменная `_avatar_cache` обеспечивает единый экземпляр:
```python
# ✅ Правильно:
cache = get_avatar_cache()

# ❌ Не создавайте новые экземпляры:
cache = AvatarCache(bot)  # Может привести к рассинхрону кэша
```

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py (post_init)
     │
     ▼
init_avatar_cache(bot)
     │
     ▼
AvatarCache.load_avatars()  ← Асинхронная задача
     │
┌────┴────┬────────────┐
▼         ▼            ▼
Telegram   data/    narrative_
Bot API  avatar_   manager.py
(file_id) cache.json  (get_avatar)
```

**Пример использования в `narrative_manager.py`:**
```python
# Получение кэша
avatar_cache = get_avatar_cache()

# Получение file_id
file_id = avatar_cache.get_avatar("vladimir_calm")

# Отправка с fallback
if file_id:
    await update.message.reply_photo(photo=file_id, caption=text)
else:
    await update.message.reply_text(text)  # Fallback на текст
```

---

## 🧪 Примеры использования

```python
# 1. Инициализация (в post_init бота)
from core.avatar_cache import init_avatar_cache

async def post_init(application: Application):
    avatar_cache = init_avatar_cache(application.bot)
    # Запускаем загрузку в фоне
    asyncio.create_task(avatar_cache.load_avatars())

# 2. Получение file_id в хендлере
from core.avatar_cache import get_avatar_cache

async def show_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = get_avatar_cache()
    file_id = cache.get_avatar("shop_keeper")
    
    if file_id:
        await update.message.reply_photo(
            photo=file_id,
            caption="🛒 Добро пожаловать в магазин!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🛒 Добро пожаловать в магазин!")

# 3. Проверка готовности перед стартом
if not avatar_cache.check_heroes_loaded():
    logger.warning("⚠️ Аватарки героев не загружены")
    # Можно отправить уведомление админу или отложить старт

# 4. Принудительное обновление кэша (отладка)
if user_id in ADMIN_IDS and command == "/reload_avatars":
    avatar_cache.clear_cache()
    await avatar_cache.load_avatars()
    await update.message.reply_text("✅ Аватарки перезагружены")
```

---

## 🛠 Чеклист при добавлении новой аватарки

1. [ ] Добавить файл изображения в папку `images/` (формат: `.jpg`, размер <10MB)
2. [ ] Добавить запись в `self.avatar_paths`:
   ```python
   "new_character": "images/new_character.jpg",
   ```
3. [ ] Использовать `snake_case` для ключа: `"new_character"`, не `"NewCharacter"`
4. [ ] Убедиться, что путь правильный относительно `BASE_DIR`
5. [ ] Перезапустить бота или вызвать `/reload_avatars` для загрузки
6. [ ] Проверить `data/avatar_cache.json` — появился ли новый `file_id`
7. [ ] Протестировать отправку через `narrative_manager.send_character_message()`

---

## 🔧 Отладка и мониторинг

**Логи при загрузке:**
```
🔍 Проверка кэша: /path/to/data/avatar_cache.json
✅ Загружено 15 записей
⏭️ Пропускаем manunya (уже в кэше)
📊 [3/20] vladimir_calm...
✅ vladimir_calm: AgACAgIAAxkBAAIC...
📊 ИТОГИ: ✅ 18 | ⚠️ 2 | 📦 20
```

**Проверка кэша вручную:**
```python
# В консоли или через админ-команду
cache = get_avatar_cache()
print(f"Загружено: {sum(1 for v in cache._cache.values() if v)}")
print(f"Пример file_id: {cache.get_avatar('manunya')[:30]}...")
```

**Очистка кэша (осторожно!):**
```bash
# Удалить файл кэша для принудительной перезагрузки
rm data/avatar_cache.json
# Перезапустить бота
```

---

*Документация актуальна для версии 2.0. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/CORE_AVATAR_CACHE.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/CORE_AVATAR_CACHE.md
   git commit -m "docs: add AvatarCache core module documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `core/vladimir_persona.py` — логика персонажа Владимира: диалоги, настроения, реакции
2. `web/api_server.py` — Flask API для веб-версии: эндпоинты, аутентификация, CORS
3. `platforms/telegram_adapter.py` — адаптер Telegram: отправка сообщений, обработка обновлений

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.