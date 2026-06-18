[#022]
Привет. Файл `database/storage.py` получил. Это критически важный модуль — «позвоночник» всей системы: хранение прогресса, статистики, подписок и шифрование персональных данных.

Ниже — готовая документация. Просто сохрани в `docs/DATABASE_STORAGE.md`.

---

## 📄 Файл: `docs/DATABASE_STORAGE.md`

```markdown
# 🗄️ PlayerStorage — Хранилище данных пользователей

> **Файл:** `database/storage.py`  
> **Версия:** 2.17 (Chaos hooks + Subscription hooks + Security) 🗄️🔐✅  
> **Ответственность:** Управление прогрессом игроков, статистикой, подписками, шифрование персональных данных (152-ФЗ)

---

## 📋 Обзор

`PlayerStorage` — единый интерфейс для работы с базой данных пользователей. Обеспечивает:

| Функция | Описание |
|---------|----------|
| 👤 Управление пользователями | Создание, чтение, обновление, удаление (CRUD) |
| 🎮 Игровое состояние | Текущий уровень, задачи, битвы с боссами, инвентарь |
| 📊 Статистика и аналитика | Логирование попыток задач, слабые зоны, точность |
| 💰 Экономика | Баланс, история очков, сезонные рейтинги |
| 🔐 Безопасность | Шифрование `parent_email` (cryptography/Fernet) |
| 🔄 Подписки | Управление тарифами, отчётами для родителей |
| 🏆 Лидерборды | Глобальные и сезонные таблицы лидеров |

**Технические особенности:**
- ✅ **SQLite** с оптимизациями: WAL-режим, кэш в памяти, таймауты
- ✅ **Singleton-соединение**: одно подключение на всё приложение
- ✅ **JSON-поля**: гибкое хранение сложных структур (инвентарь, профили)
- ✅ **Миграции**: автоматическое добавление новых колонок при запуске
- ✅ **152-ФЗ**: шифрование персональных данных родителей

---

## ⚙️ Инициализация и подключение

### Глобальное соединение (Singleton)

```python
_connection = None

def get_connection():
    """Возвращает ОДНО соединение на всё приложение."""
    global _connection
    
    if _connection is None:
        ensure_data_dir()
        _connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        
        # ✅ OPTIMIZATIONS FOR CONCURRENCY
        _connection.execute("PRAGMA journal_mode=WAL")      # Параллельное чтение/запись
        _connection.execute("PRAGMA synchronous=NORMAL")    # Баланс скорости/надёжности
        _connection.execute("PRAGMA busy_timeout=5000")     # Ждать 5 сек при блокировке
        _connection.execute("PRAGMA cache_size=-64000")     # 64 MB кэш в памяти
        _connection.execute("PRAGMA temp_store=MEMORY")     # Временные таблицы в RAM
    
    return _connection
```

> ⚠️ **Важно:** `check_same_thread=False` разрешает использование соединения из разных потоков. Это безопасно при правильном управлении транзакциями.

### Инициализация PlayerStorage

```python
storage = PlayerStorage()
```

**Что происходит при инициализации:**
1. Получается глобальное соединение через `get_connection()`
2. Проверяются и создаются недостающие колонки в таблице `users`:
   - Chaos System: `consecutive_errors`, `chaos_energy`, `rift_stage`, ...
   - Dynamic Difficulty: `difficulty_level_*`, `accuracy_last_10`
   - Monetization: `parent_email`, `subscription_tier`, `report_preferences`
   - Stats: `total_tasks_attempted`, `accuracy_overall`, ...
3. Создаются служебные таблицы:
   - `task_attempts` — детальный лог попыток задач
   - `subscriptions` — информация о подписках

---

## 🔐 Шифрование персональных данных (152-ФЗ)

Для соответствия требованиям по защите персональных данных, поле `parent_email` шифруется перед сохранением.

```python
# 🔐 Шифрование при сохранении
def _encrypt_parent_data(data: str) -> str:
    if not data or not _fernet:
        return data
    return _fernet.encrypt(data.encode()).decode()

# 🔐 Расшифровка при чтении
def _decrypt_parent_data(encrypted: str) -> str:
    if not encrypted or not _fernet:
        return encrypted
    return _fernet.decrypt(encrypted.encode()).decode()
```

**Требования:**
- Ключ шифрования хранится в `config.PARENT_DATA_KEY` (не в коде!)
- Если `cryptography` не установлен — шифрование отключается с предупреждением в логе
- Расшифровка происходит только внутри `_deserialize_row()`, внешнему коду передаётся уже расшифрованное значение

> ⚠️ **Безопасность:** Никогда не логируйте и не выводите в интерфейс сырые зашифрованные значения.

---

## 🗄️ Структура данных

### Категории полей

| Категория | Поля | Хранение в БД |
|-----------|------|--------------|
| **Базовые** | `user_id`, `username`, `level`, `xp`, `total_score`, `score_balance` | Отдельные колонки |
| **JSON-массивы** | `inventory`, `unlocked_zones`, `defeated_bosses`, `abilities` | TEXT (JSON) |
| **JSON-объекты** | `achievements`, `artifact_upgrades`, `bank_data`, `castle_data`, `player_profile` | TEXT (JSON) |
| **Game State** | `current_level`, `in_boss_battle`, `boss_health`, `consecutive_errors`, ... | Упакованы в JSON-колонку `game_state` |
| **Статистика** | `total_tasks_attempted`, `accuracy_overall`, `last_session_end` | Отдельные колонки |
| **Монетизация** | `parent_email` (зашифровано), `subscription_tier`, `report_preferences` | Отдельные колонки + JSON |

### Сериализация/Десериализация

**При сохранении (`_serialize_for_db`):**
```python
# JSON-поля → строка JSON
result['inventory'] = json.dumps(data['inventory'], ensure_ascii=False)

# Game State → отдельная JSON-колонка
game_state = {k: data[k] for k in GAME_STATE_FIELDS if k in data}
result['game_state'] = json.dumps(game_state, ensure_ascii=False)

# parent_email → шифрование
if key == 'parent_email' and value:
    result[key] = _encrypt_parent_data(value)
```

**При чтении (`_deserialize_row`):**
```python
# Строка JSON → Python-объект
for field in JSON_FIELDS:
    data[field] = json.loads(row[field]) if row[field] else default

# Распаковка game_state в корень объекта
if row['game_state']:
    data.update(json.loads(row['game_state']))

# parent_email → расшифровка
if 'parent_email' in data and data['parent_email']:
    data['parent_email'] = _decrypt_parent_data(data['parent_email'])
```

---

## 👤 Управление пользователями

### `get_or_create_user(user_id, username=None, first_name=None) -> Dict` 🎯
Получает пользователя или создаёт нового с дефолтными значениями.

**Логика:**
```
1. Извлечь числовой user_id из строки (поддержка "telegram_123456")
2. SELECT * FROM users WHERE user_id = ?
3. Если найден:
   ├─ Десериализовать строки в объекты
   ├─ Обновить username если изменился
   └─ Вернуть словарь
4. Если не найден:
   ├─ Создать default_data со всеми полями
   ├─ Сериализовать для БД
   ├─ Вставить запись (INSERT)
   └─ Вернуть default_data
```

**Дефолтные значения для нового пользователя:**
```python
{
    "level": 1, "xp": 0, "xp_to_next": 50,
    "total_score": 0, "score_balance": 0,
    "unlocked_zones": ["addition"],  # Начинаем с мира "Сложение"
    "inventory": [], "achievements": {}, "artifact_upgrades": {},
    "castle_data": {"decorations": [], "upkeep_paid_until": None},
    "player_profile": { ... },  # Профиль с метриками поведения
    "first_time": True,  # Показывать обучение
    # 🔹 Новые поля
    "consecutive_errors": 0, "chaos_energy": 0, "rift_stage": 0,
    "subscription_tier": "free", "parent_email": None,
    "total_tasks_attempted": 0, "accuracy_overall": 1.0
}
```

---

### `save_user(user_id, data: Dict) -> bool`
Сохраняет изменения пользователя в БД.

**Особенности:**
- Автоматически обновляет `updated_at`
- Поддерживает upsert: если пользователь не найден → создаёт запись
- Логирует ключевые поля: `total_score`, `score_balance`, `player_profile`
- Возвращает `True` при успехе, `False` при ошибке (с rollback)

**Пример:**
```python
user_data = storage.get_user(123456)
user_data["score_balance"] += 50
user_data["inventory"].append("potion_health")
storage.save_user(123456, user_data)
```

---

### `get_user(user_id) -> Optional[Dict]`
Получает данные пользователя по ID.

**Возвращает:**
- Полный словарь с десериализованными полями
- `None` если пользователь не найден

---

### `delete_user(user_id)`
Удаляет пользователя и все связанные данные (каскадное удаление).

**Удаляет из таблиц:**
- `users` — основная запись
- `score_log` — история очков
- `task_history` — история задач (устаревшая)
- `task_attempts` — детальные попытки
- `subscriptions` — подписки

> ⚠️ **Необратимо!** Используйте только по явному запросу пользователя или для тестов.

---

## 📊 Статистика и аналитика

### `log_task_attempt(...)` 🎯
Записывает детальную информацию о попытке решения задачи.

**Параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `user_id` | `int` | ID пользователя |
| `task_id` | `str` | Уникальный идентификатор задачи |
| `island_id` | `str` | ID мира/острова (`addition`, `multiplication`) |
| `operation_type` | `str` | Тип операции (`addition`, `multiply`) |
| `is_correct` | `bool` | Был ли ответ верным |
| `time_taken` | `float` | Время решения в секундах (опционально) |
| `answer_given` | `str` | Ответ пользователя |
| `expected_answer` | `str` | Правильный ответ |
| `chaos_energy` | `int` | Уровень хаоса на момент попытки |
| `rift_stage` | `int` | Стадия Разлома |
| `transfer_used` | `bool` | Была ли использована задача-перенос |

**Использование:**
```python
storage.log_task_attempt(
    user_id=123456,
    task_id="add_042",
    island_id="addition",
    operation_type="addition",
    is_correct=True,
    time_taken=3.2,
    answer_given="15",
    expected_answer="15",
    chaos_energy=20,
    rift_stage=1,
    transfer_used=False
)
```

---

### `get_user_weaknesses(user_id, limit=5) -> List[Dict]`
Анализирует историю попыток и возвращает слабые зоны пользователя.

**Логика запроса:**
```sql
SELECT 
    island_id, operation_type,
    COUNT(*) as total,
    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
    ROUND(1.0 * correct / total * 100, 1) as accuracy
FROM task_attempts
WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
GROUP BY island_id, operation_type
HAVING COUNT(*) >= 3  -- Минимум 3 попытки для статистической значимости
ORDER BY accuracy ASC  -- Сначала самые слабые
LIMIT ?
```

**Возвращаемое значение:**
```python
[
    {
        "island_id": "division",
        "operation_type": "division",
        "total": 12,
        "correct": 4,
        "accuracy": 33.3  # Низкая точность → слабая зона
    },
    # ...
]
```

**Использование:**
```python
weaknesses = storage.get_user_weaknesses(123456)
for zone in weaknesses:
    if zone["accuracy"] < 50:
        # Предложить тренировку по этой теме
        suggest_practice(zone["island_id"], zone["operation_type"])
```

---

## 💰 Подписки и монетизация

### `get_subscription_info(user_id) -> Dict`
Возвращает информацию о подписке пользователя.

**Возвращаемое значение:**
```python
{
    "subscription_status": "premium",  # "free", "premium", "family"
    "subscription_start": "2026-04-01T10:00:00Z",
    "subscription_end": "2026-05-01T10:00:00Z",
    "report_frequency": "weekly"  # "daily", "weekly", "monthly"
}
```

---

### `update_subscription(user_id, status, parent_email=None, frequency='weekly') -> bool`
Обновляет или создаёт запись о подписке.

**Особенности:**
- `parent_email` автоматически шифруется перед сохранением
- Использует `INSERT OR REPLACE` для обновления существующей записи
- Устанавливает `subscription_start = datetime('now')` при активации

**Пример:**
```python
storage.update_subscription(
    user_id=123456,
    status="premium",
    parent_email="parent@example.com",  # Будет зашифровано
    frequency="weekly"
)
```

---

## 🏆 Очки и лидерборды

### `log_score_change(user_id, amount, reason, context=None, season_id=None) -> bool`
Записывает изменение счёта в историю.

**Параметры:**
| Параметр | Тип | Описание | Пример |
|----------|-----|----------|--------|
| `amount` | `int` | Сумма изменения (положительная или отрицательная) | `+50`, `-25` |
| `reason` | `str` | Причина изменения | `"task_correct"`, `"shop_purchase"` |
| `context` | `str` | Дополнительный контекст | `"island:addition,task:42"` |
| `season_id` | `int` | ID сезона (для сезонных рейтингов) | `1`, `2` |

---

### `get_leaderboard(period='all', limit=10, season_id=None) -> List[Dict]`
Возвращает таблицу лидеров.

**Режимы `period`:**
| Значение | Описание |
|----------|----------|
| `'all'` | Глобальный рейтинг по `total_score` |
| `'week'` | Рейтинг за последние 7 дней (по `net_score`) |
| `'month'` | Рейтинг за последние 30 дней |
| `'season'` | Рейтинг текущего сезона (требуется `season_id`) |

**Возвращаемое значение:**
```python
[
    {
        "user_id": 123456,
        "username": "Морковка",
        "level": 5,
        "earned": 1250,   # Заработано за период
        "spent": 300,     # Потрачено за период
        "net_score": 950  # Чистый прирост
    },
    # ...
]
```

---

## 🔧 Вспомогательные методы

### `_extract_numeric_user_id(user_id) -> int`
Извлекает числовой ID из строки формата `platform_123456`.

**Поддерживаемые форматы:**
```
"123456"           → 123456
"telegram_123456"  → 123456
"vk_789012"        → 789012
"max_ru_345678"    → 345678
```

**Зачем это нужно:**
- Единая обработка ID от разных платформ (Telegram, VK, MAX)
- Гарантия, что в БД хранятся только числовые ключи

---

### `close()`
Завершает работу хранилища.

> ⚠️ **Важно:** Метод **не закрывает** глобальное соединение, так как оно может использоваться другими компонентами приложения. Для полного завершения работы приложения закрывайте соединение вручную при необходимости.

---

## ⚠️ Важные замечания

### 1. Глобальное соединение и многопоточность
```python
_connection = sqlite3.connect(DB_FILE, check_same_thread=False)
```
- `check_same_thread=False` разрешает использование из разных потоков
- **Безопасно** при условии:
  - Все запросы выполняются через курсоры
  - Транзакции завершаются (`commit()`/`rollback()`)
  - Нет длительных блокировок

### 2. Миграции схемы
Новые колонки добавляются автоматически при инициализации:
```python
def _ensure_chaos_columns(self):
    # Проверяет наличие колонок → добавляет если нет
```
**Преимущество:** Не требуется ручное выполнение миграций при обновлении бота.

### 3. Обработка `None` и дефолтов
Метод `_deserialize_row()` гарантирует, что все поля имеют значения:
```python
if data.get('total_score') is None:
    data['total_score'] = 0  # Никогда не возвращаем None для критичных полей
```

### 4. Шифрование и безопасность
- Ключ шифрования **не должен** храниться в коде или репозитории
- Используйте переменные окружения: `PARENT_DATA_KEY=your_key_here`
- При утечке ключа — немедленно смените его и перешифруйте данные

### 5. Производительность
- Включён WAL-режим для параллельного чтения/записи
- Кэш 64 MB уменьшает дисковые операции
- Индексы на `task_attempts(user_id, timestamp)` ускоряют аналитику

**Мониторинг:**
```python
# Проверка размера БД
import os
size_mb = os.path.getsize("data/progress.db") / 1024 / 1024
logger.info(f"📦 Размер БД: {size_mb:.2f} MB")
```

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py
     │
     ▼
PlayerStorage (storage.py)
     │
┌────┴────┬────────────┬────────────┬────────────┐
▼         ▼            ▼            ▼            ▼
ChislyandiaEngine  ScoreManager  NarrativeManager  (аналитика)
(прогресс)        (очки)        (профили)         (слабые зоны)
     │                │            │                │
     ▼                ▼            ▼                ▼
users table     score_log    player_profile   task_attempts
(основные)      (история)    (поведение)      (детали задач)
```

---

## 🧪 Примеры использования

```python
# 1. Получение или создание пользователя
user = storage.get_or_create_user(
    user_id="telegram_123456",
    username="Morcovka",
    first_name="Морковка"
)
print(f"Уровень: {user['level']}, Баланс: {user['score_balance']}")

# 2. Обновление прогресса
user["level"] = 2
user["xp"] = 75
user["unlocked_zones"].append("subtraction")
storage.save_user(123456, user)

# 3. Логирование попытки задачи
storage.log_task_attempt(
    user_id=123456,
    task_id="sub_015",
    island_id="subtraction",
    operation_type="subtraction",
    is_correct=False,
    time_taken=5.1,
    answer_given="3",
    expected_answer="5",
    chaos_energy=40,
    rift_stage=2
)

# 4. Анализ слабых зон
weaknesses = storage.get_user_weaknesses(123456)
for zone in weaknesses:
    print(f"Слабая зона: {zone['island_id']}/{zone['operation_type']} — точность {zone['accuracy']}%")

# 5. Активация подписки
storage.update_subscription(
    user_id=123456,
    status="premium",
    parent_email="parent@example.com",
    frequency="weekly"
)

# 6. Получение лидерборда за неделю
leaderboard = storage.get_leaderboard(period="week", limit=5)
for i, entry in enumerate(leaderboard, 1):
    print(f"{i}. {entry['username']} — +{entry['net_score']} за неделю")
```

---

## 🛠 Чеклист при добавлении нового поля

1. [ ] Добавить поле в `DB_COLUMNS` (если нужна отдельная колонка)
2. [ ] Добавить в `JSON_FIELDS` или `GAME_STATE_FIELDS` (если часть JSON)
3. [ ] Добавить миграцию в соответствующий `_ensure_*_columns()` метод
4. [ ] Обновить `_deserialize_row()`: задать дефолтное значение при `None`
5. [ ] Обновить `_serialize_for_db()`: обработать сериализацию/шифрование
6. [ ] Обновить `get_or_create_user()`: добавить дефолт для новых пользователей
7. [ ] Протестировать: создать нового пользователя → проверить, что поле инициализировано
8. [ ] Если поле содержит персональные данные → добавить шифрование через `_encrypt_parent_data()`

---

*Документация актуальна для версии 2.17. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/DATABASE_STORAGE.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/DATABASE_STORAGE.md
   git commit -m "docs: add PlayerStorage database documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `core/avatar_cache.py` — кэширование аватарок, загрузка из Telegram API
2. `core/vladimir_persona.py` — логика персонажа Владимира, диалоги, настроения
3. `web/api_server.py` — Flask API для веб-версии, эндпоинты, аутентификация

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.