[#026]
Привет. Файл `database/schema.py` получил. Это фундаментальный модуль — схема базы данных, которая определяет структуру хранения всех данных «Числяндии».

Ниже — готовая документация. Просто сохрани в `docs/DATABASE_SCHEMA.md`.

---

## 📄 Файл: `docs/DATABASE_SCHEMA.md`

```markdown
# 🗄️ Database Schema — Схема базы данных

> **Файл:** `database/schema.py`  
> **Версия:** 2.2 (Златочёт + bank_data поле) 🏦🗄️  
> **Ответственность:** Создание и миграция таблиц SQLite, определение структуры данных пользователей, логов и истории задач

---

## 📋 Обзор

`schema.py` — модуль инициализации базы данных. При запуске бота он:

| Действие | Описание |
|----------|----------|
| ✅ Создание таблиц | `users`, `score_log`, `task_history` если не существуют |
| 🔧 Миграции | Автоматическое добавление новых колонок при обновлении версии |
| 📊 Индексы | Оптимизация запросов по `user_id`, `total_score`, `created_at` |
| 🗂️ Пути | Определение пути к `data/progress.db` относительно корня проекта |

```
┌─────────────────┐
│   schema.py     │
├─────────────────┤
│ • init_database()│ ← Создание/обновление БД
│ • get_db_path()  │ ← Путь к файлу БД
│ • _run_migrations│ ← Применение миграций
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite БД     │
│   progress.db   │
├─────────────────┤
│ • users         │ ← Профили игроков (основная)
│ • score_log     │ ← История изменений очков
│ • task_history  │ ← История решений задач
└─────────────────┘
```

---

## 🗂️ Таблицы базы данных

### 📋 Таблица `users` — Профили игроков

**Основная таблица**, хранит все данные пользователя.

| Группа полей | Поле | Тип | По умолчанию | Описание |
|-------------|------|-----|-------------|----------|
| **Идентификация** | `user_id` | `INTEGER` | — | **PRIMARY KEY**, числовой ID пользователя |
| | `username` | `TEXT` | `NULL` | Имя пользователя в мессенджере |
| | `first_name` | `TEXT` | `NULL` | Имя/никнейм для отображения |
| **🎮 Прогресс** | `level` | `INTEGER` | `1` | Текущий уровень игрока |
| | `xp` | `INTEGER` | `0` | Накопленный опыт |
| | `xp_to_next` | `INTEGER` | `50` | Опыт до следующего уровня |
| **💰 Очки** | `total_score` | `INTEGER` | `0` | Общий счёт за всё время (рейтинг) |
| | `score_balance` | `INTEGER` | `0` | Доступные очки для трат |
| | `season_score` | `INTEGER` | `0` | Счёт текущего сезона |
| | `season_id` | `INTEGER` | `1` | ID текущего сезона |
| **📊 Статистика** | `tasks_solved` | `INTEGER` | `0` | Всего попыток задач |
| | `tasks_correct` | `INTEGER` | `0` | Правильных ответов |
| **🎒 Контент (JSON)** | `defeated_bosses` | `TEXT` | `'[]'` | Список побеждённых боссов |
| | `completed_zones` | `TEXT` | `'[]'` | Пройденные миры/острова |
| | `inventory` | `TEXT` | `'[]'` | Предметы в инвентаре |
| | `unlocked_zones` | `TEXT` | `'["addition"]'` | Разблокированные миры |
| | `rewards` | `TEXT` | `'[]'` | Полученные награды |
| | `abilities` | `TEXT` | `'[]'` | Активные способности |
| | `achievements` | `TEXT` | `'{}'` | Достижения (dict) |
| | `castle_decorations` | `TEXT` | `'[]'` | Декорации замка |
| | `artifact_upgrades` | `TEXT` | `'{}'` | Уровни артефактов (dict) |
| **🏦 Банк (Златочёт)** | `bank_data` | `TEXT` | `'{}'` | Данные вклада: баланс, проценты, даты |
| **⚙️ Состояние игры** | `game_state` | `TEXT` | `'{}'` | Временное состояние: текущая задача, битва с боссом и т.д. |
| **📅 Мета-данные** | `created_at` | `TIMESTAMP` | `CURRENT_TIMESTAMP` | Дата регистрации |
| | `updated_at` | `TIMESTAMP` | `CURRENT_TIMESTAMP` | Дата последнего обновления |

> ⚠️ **Важно:** Поля с типом `TEXT` и значением по умолчанию `'[]'` или `'{}'` хранят **JSON-строки**. При чтении их нужно десериализовать через `json.loads()`, при записи — сериализовать через `json.dumps()`.

---

### 📋 Таблица `score_log` — История изменений очков

Журнал всех операций с очками для аналитики и отладки.

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `id` | `INTEGER` | **PRIMARY KEY**, автоинкремент | `1`, `2`, `3` |
| `user_id` | `INTEGER` | Ссылка на `users.user_id` | `123456` |
| `amount` | `INTEGER` | Изменение очков (+ или -) | `+50`, `-25` |
| `reason` | `TEXT` | Причина изменения | `"task_correct"`, `"shop_purchase"` |
| `context` | `TEXT` | Дополнительный контекст | `"island:addition,task:42"` |
| `season_id` | `INTEGER` | Сезон, к которому относится запись | `1` |
| `created_at` | `TIMESTAMP` | Время операции | `"2026-04-05 14:30:00"` |

**Пример использования:**
```sql
-- Найти все покупки в магазине за последнюю неделю
SELECT * FROM score_log 
WHERE user_id = 123456 
  AND reason = 'shop_purchase'
  AND created_at >= datetime('now', '-7 days');
```

---

### 📋 Таблица `task_history` — История решений задач

Упрощённый лог попыток решения задач (для базовой статистики).

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `id` | `INTEGER` | **PRIMARY KEY**, автоинкремент | `1`, `2`, `3` |
| `user_id` | `INTEGER` | Ссылка на `users.user_id` | `123456` |
| `task_type` | `TEXT` | Тип задачи | `"addition"`, `"multiplication"` |
| `difficulty` | `TEXT` | Сложность | `"easy"`, `"hard"` |
| `is_correct` | `INTEGER` | Был ли ответ верным (1/0) | `1`, `0` |
| `time_spent` | `REAL` | Время решения в секундах | `3.2`, `12.5` |
| `timestamp` | `TIMESTAMP` | Время попытки | `"2026-04-05 14:30:00"` |

> ⚠️ **Примечание:** Для детальной аналитики используется таблица `task_attempts` (создаётся в `PlayerStorage._ensure_task_attempts_table()`), а не `task_history`.

---

## 📊 Индексы

Для ускорения частых запросов созданы следующие индексы:

| Индекс | Таблица | Поле | Назначение |
|--------|---------|------|-----------|
| `idx_users_id` | `users` | `user_id` | Быстрый поиск профиля по ID |
| `idx_users_score` | `users` | `total_score DESC` | Быстрая сортировка лидерборда |
| `idx_log_user` | `score_log` | `user_id` | Быстрый поиск истории очков пользователя |
| `idx_log_time` | `score_log` | `created_at` | Фильтрация по времени (неделя/месяц) |
| `idx_history_user` | `task_history` | `user_id` | Быстрый поиск истории задач |

---

## 🔧 Миграции

Функция `_run_migrations(cursor, conn)` автоматически применяет изменения схемы при обновлении бота.

**Текущая миграция (версия 2.2):**
```python
if 'bank_data' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN bank_data TEXT DEFAULT '{}'")
```

**Как добавить новую миграцию:**
1. Получить список колонок: `cursor.execute("PRAGMA table_info(users)")`
2. Проверить наличие новой колонки
3. Если нет → выполнить `ALTER TABLE ADD COLUMN ...`
4. Закоммитить изменения: `conn.commit()`

**Пример для будущего поля `preferred_difficulty`:**
```python
if 'preferred_difficulty' not in columns:
    logger.info("🔄 Миграция
[#026]
Привет. Файл `database/schema.py` получил. Это фундаментальный модуль — схема базы данных, которая определяет структуру хранения всех данных «Числяндии».

Ниже — готовая документация. Просто сохрани в `docs/DATABASE_SCHEMA.md`.

---

## 📄 Файл: `docs/DATABASE_SCHEMA.md`

```markdown
# 🗄️ Database Schema — Схема базы данных

> **Файл:** `database/schema.py`  
> **Версия:** 2.2 (Златочёт + bank_data поле) 🏦🗄️  
> **Ответственность:** Создание и миграция таблиц SQLite, определение структуры данных пользователей, логов и истории задач

---

## 📋 Обзор

`schema.py` — модуль инициализации базы данных. При запуске бота он:

| Действие | Описание |
|----------|----------|
| ✅ Создание таблиц | `users`, `score_log`, `task_history` если не существуют |
| 🔧 Миграции | Автоматическое добавление новых колонок при обновлении версии |
| 📊 Индексы | Оптимизация запросов по `user_id`, `total_score`, `created_at` |
| 🗂️ Пути | Определение пути к `data/progress.db` относительно корня проекта |

```
┌─────────────────┐
│   schema.py     │
├─────────────────┤
│ • init_database()│ ← Создание/обновление БД
│ • get_db_path()  │ ← Путь к файлу БД
│ • _run_migrations│ ← Применение миграций
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite БД     │
│   progress.db   │
├─────────────────┤
│ • users         │ ← Профили игроков (основная)
│ • score_log     │ ← История изменений очков
│ • task_history  │ ← История решений задач
└─────────────────┘
```

---

## 🗂️ Таблицы базы данных

### 📋 Таблица `users` — Профили игроков

**Основная таблица**, хранит все данные пользователя.

| Группа полей | Поле | Тип | По умолчанию | Описание |
|-------------|------|-----|-------------|----------|
| **Идентификация** | `user_id` | `INTEGER` | — | **PRIMARY KEY**, числовой ID пользователя |
| | `username` | `TEXT` | `NULL` | Имя пользователя в мессенджере |
| | `first_name` | `TEXT` | `NULL` | Имя/никнейм для отображения |
| **🎮 Прогресс** | `level` | `INTEGER` | `1` | Текущий уровень игрока |
| | `xp` | `INTEGER` | `0` | Накопленный опыт |
| | `xp_to_next` | `INTEGER` | `50` | Опыт до следующего уровня |
| **💰 Очки** | `total_score` | `INTEGER` | `0` | Общий счёт за всё время (рейтинг) |
| | `score_balance` | `INTEGER` | `0` | Доступные очки для трат |
| | `season_score` | `INTEGER` | `0` | Счёт текущего сезона |
| | `season_id` | `INTEGER` | `1` | ID текущего сезона |
| **📊 Статистика** | `tasks_solved` | `INTEGER` | `0` | Всего попыток задач |
| | `tasks_correct` | `INTEGER` | `0` | Правильных ответов |
| **🎒 Контент (JSON)** | `defeated_bosses` | `TEXT` | `'[]'` | Список побеждённых боссов |
| | `completed_zones` | `TEXT` | `'[]'` | Пройденные миры/острова |
| | `inventory` | `TEXT` | `'[]'` | Предметы в инвентаре |
| | `unlocked_zones` | `TEXT` | `'["addition"]'` | Разблокированные миры |
| | `rewards` | `TEXT` | `'[]'` | Полученные награды |
| | `abilities` | `TEXT` | `'[]'` | Активные способности |
| | `achievements` | `TEXT` | `'{}'` | Достижения (dict) |
| | `castle_decorations` | `TEXT` | `'[]'` | Декорации замка |
| | `artifact_upgrades` | `TEXT` | `'{}'` | Уровни артефактов (dict) |
| **🏦 Банк (Златочёт)** | `bank_data` | `TEXT` | `'{}'` | Данные вклада: баланс, проценты, даты |
| **⚙️ Состояние игры** | `game_state` | `TEXT` | `'{}'` | Временное состояние: текущая задача, битва с боссом и т.д. |
| **📅 Мета-данные** | `created_at` | `TIMESTAMP` | `CURRENT_TIMESTAMP` | Дата регистрации |
| | `updated_at` | `TIMESTAMP` | `CURRENT_TIMESTAMP` | Дата последнего обновления |

> ⚠️ **Важно:** Поля с типом `TEXT` и значением по умолчанию `'[]'` или `'{}'` хранят **JSON-строки**. При чтении их нужно десериализовать через `json.loads()`, при записи — сериализовать через `json.dumps()`.

---

### 📋 Таблица `score_log` — История изменений очков

Журнал всех операций с очками для аналитики и отладки.

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `id` | `INTEGER` | **PRIMARY KEY**, автоинкремент | `1`, `2`, `3` |
| `user_id` | `INTEGER` | Ссылка на `users.user_id` | `123456` |
| `amount` | `INTEGER` | Изменение очков (+ или -) | `+50`, `-25` |
| `reason` | `TEXT` | Причина изменения | `"task_correct"`, `"shop_purchase"` |
| `context` | `TEXT` | Дополнительный контекст | `"island:addition,task:42"` |
| `season_id` | `INTEGER` | Сезон, к которому относится запись | `1` |
| `created_at` | `TIMESTAMP` | Время операции | `"2026-04-05 14:30:00"` |

**Пример использования:**
```sql
-- Найти все покупки в магазине за последнюю неделю
SELECT * FROM score_log 
WHERE user_id = 123456 
  AND reason = 'shop_purchase'
  AND created_at >= datetime('now', '-7 days');
```

---

### 📋 Таблица `task_history` — История решений задач

Упрощённый лог попыток решения задач (для базовой статистики).

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `id` | `INTEGER` | **PRIMARY KEY**, автоинкремент | `1`, `2`, `3` |
| `user_id` | `INTEGER` | Ссылка на `users.user_id` | `123456` |
| `task_type` | `TEXT` | Тип задачи | `"addition"`, `"multiplication"` |
| `difficulty` | `TEXT` | Сложность | `"easy"`, `"hard"` |
| `is_correct` | `INTEGER` | Был ли ответ верным (1/0) | `1`, `0` |
| `time_spent` | `REAL` | Время решения в секундах | `3.2`, `12.5` |
| `timestamp` | `TIMESTAMP` | Время попытки | `"2026-04-05 14:30:00"` |

> ⚠️ **Примечание:** Для детальной аналитики используется таблица `task_attempts` (создаётся в `PlayerStorage._ensure_task_attempts_table()`), а не `task_history`.

---

## 📊 Индексы

Для ускорения частых запросов созданы следующие индексы:

| Индекс | Таблица | Поле | Назначение |
|--------|---------|------|-----------|
| `idx_users_id` | `users` | `user_id` | Быстрый поиск профиля по ID |
| `idx_users_score` | `users` | `total_score DESC` | Быстрая сортировка лидерборда |
| `idx_log_user` | `score_log` | `user_id` | Быстрый поиск истории очков пользователя |
| `idx_log_time` | `score_log` | `created_at` | Фильтрация по времени (неделя/месяц) |
| `idx_history_user` | `task_history` | `user_id` | Быстрый поиск истории задач |

---

## 🔧 Миграции

Функция `_run_migrations(cursor, conn)` автоматически применяет изменения схемы при обновлении бота.

**Текущая миграция (версия 2.2):**
```python
if 'bank_data' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN bank_data TEXT DEFAULT '{}'")
```

**Как добавить новую миграцию:**
1. Получить список колонок: `cursor.execute("PRAGMA table_info(users)")`
2. Проверить наличие новой колонки
3. Если нет → выполнить `ALTER TABLE ADD COLUMN ...`
4. Закоммитить изменения: `conn.commit()`

**Пример для будущего поля `preferred_difficulty`:**
```python
if 'preferred_difficulty' not in columns:
    logger.info("🔄 Миграция: добавляем preferred_difficulty...")
    cursor.execute("ALTER TABLE users ADD COLUMN preferred_difficulty TEXT DEFAULT 'medium'")
    conn.commit()
```

---

## ⚠️ Важные замечания

### 1. JSON-поля в SQLite
SQLite не имеет нативного типа `JSON`. Все сложные структуры хранятся как `TEXT` с сериализацией:

```python
# Запись (в storage.py):
user_data["inventory"] = json.dumps(["potion_health", "ring_power"], ensure_ascii=False)

# Чтение (в storage.py):
inventory = json.loads(user_row["inventory"]) if user_row["inventory"] else []
```

**Рекомендации:**
- Всегда используйте `ensure_ascii=False` для поддержки кириллицы
- Обрабатывайте `json.JSONDecodeError` при чтении (старые записи могут быть битыми)
- Для новых полей задавайте дефолт `'[]'` для списков, `'{}'` для словарей

### 2. Внешние ключи
SQLite поддерживает `FOREIGN KEY`, но по умолчанию не проверяет их. Для включения:
```python
conn.execute("PRAGMA foreign_keys = ON")
```
> ⚠️ В текущей реализации внешние ключи декларированы, но не включены. Это допустимо для одиночного процесса, но может привести к «висячим» записям при ручном редактировании БД.

### 3. Пути к БД
Функция `get_db_path()` возвращает путь относительно расположения `schema.py`:
```python
os.path.join(os.path.dirname(__file__), "..", "data", "progress.db")
```
**Структура:**
```
project_root/
├── database/
│   └── schema.py
├── data/
│   └── progress.db  ← сюда создаётся БД
└── ...
```

### 4. Безопасность
- **Никогда не храните** токены, пароли или персональные данные в БД без шифрования
- Для `parent_email` используется шифрование через `cryptography.fernet` (в `storage.py`)
- Регулярно делайте бэкапы `progress.db` перед обновлениями

### 5. Типы данных SQLite
| Python тип | SQLite тип | Примечание |
|-----------|-----------|-----------|
| `int` | `INTEGER` | Автоматическое преобразование |
| `float` | `REAL` | Для `time_spent` |
| `str` | `TEXT` | Для JSON, строк, дат |
| `datetime` | `TEXT` | Хранить как ISO-строку: `datetime.isoformat()` |

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py
     │
     ▼
database/storage.py (PlayerStorage)
     │
     ▼
database/schema.py (init_database)
     │
     ▼
SQLite: progress.db
     │
┌────┴────┬────────────┐
▼         ▼            ▼
users   score_log   task_history
(профиль) (очки)    (статистика)
     │
     ▼
core/game_engine.py  ← читает/пишет прогресс
core/score_manager.py ← логирует изменения очков
```

---

## 🧪 Примеры использования

### 1. Инициализация БД при старте бота
```python
# В manyunya_bot.py или config.py
from database.schema import init_database

init_database()  # Создаёт/обновляет таблицы
```

### 2. Прямой запрос к БД (для отладки)
```python
import sqlite3
from database.schema import get_db_path

conn = sqlite3.connect(get_db_path())
cursor = conn.cursor()

# Посчитать пользователей с балансом > 1000
cursor.execute(
    "SELECT COUNT(*) FROM users WHERE score_balance > ?",
    (1000,)
)
count = cursor.fetchone()[0]
print(f"Богатых игроков: {count}")

conn.close()
```

### 3. Экспорт статистики
```sql
-- Экспорт в CSV (через sqlite3 CLI):
sqlite3 data/progress.db ".mode csv" ".headers on" \
  "SELECT user_id, username, level, total_score FROM users ORDER BY total_score DESC LIMIT 10" \
  > leaderboard.csv
```

### 4. Проверка целостности БД
```python
import sqlite3
from database.schema import get_db_path

conn = sqlite3.connect(get_db_path())
cursor = conn.cursor()

# Проверка целостности
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()[0]
if result == "ok":
    print("✅ БД в порядке")
else:
    print(f"❌ Ошибка целостности: {result}")

conn.close()
```

---

## 🛠 Чеклист при изменении схемы

1. [ ] Добавить новое поле в `CREATE TABLE` (для новых установок)
2. [ ] Добавить миграцию в `_run_migrations()` (для существующих БД)
3. [ ] Обновить `PlayerStorage.DB_COLUMNS` и `JSON_FIELDS` если поле новое
4. [ ] Добавить поле в `_deserialize_row()` и `_serialize_for_db()` в `storage.py`
5. [ ] Задать дефолтное значение для новых пользователей в `get_or_create_user()`
6. [ ] Протестировать на чистой БД и на существующей (с миграцией)
7. [ ] Обновить документацию (этот файл)

---

## 🔍 Отладка и мониторинг

### Просмотр структуры таблицы
```bash
sqlite3 data/progress.db ".schema users"
```

### Размер БД
```python
import os
size_mb = os.path.getsize("data/progress.db") / 1024 / 1024
print(f"📦 Размер БД: {size_mb:.2f} MB")
```

### Количество записей
```sql
SELECT 
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM score_log) as score_logs,
  (SELECT COUNT(*) FROM task_history) as task_history;
```

### Поиск «битых» JSON-полей
```python
import json
import sqlite3

conn = sqlite3.connect("data/progress.db")
cursor = conn.cursor()
cursor.execute("SELECT user_id, inventory FROM users")

for user_id, inventory_json in cursor.fetchall():
    if inventory_json:
        try:
            json.loads(inventory_json)
        except json.JSONDecodeError:
            print(f"❌ Битый JSON у пользователя {user_id}: {inventory_json[:50]}...")

conn.close()
```

---

## 🔄 Расширение: добавление новой таблицы

Чтобы добавить таблицу `user_settings` (например, для настроек уведомлений):

1. **Добавить CREATE TABLE в `init_database()`:**
```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        notifications_enabled INTEGER DEFAULT 1,
        language TEXT DEFAULT 'ru',
        theme TEXT DEFAULT 'light',
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
""")
```

2. **Добавить индекс:**
```python
cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_user ON user_settings(user_id)")
```

3. **Обновить `PlayerStorage`:**
   - Добавить методы `get_user_settings()`, `update_user_settings()`
   - Обеспечить сериализацию если будут JSON-поля

4. **Протестировать миграцию** на существующей БД

---

*Документация актуальна для версии 2.2. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/DATABASE_SCHEMA.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/DATABASE_SCHEMA.md
   git commit -m "docs: add database schema documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `platforms/telegram_adapter.py` — адаптер Telegram: отправка сообщений, обработка обновлений
2. `platforms/max_adapter.py` — адаптер VK/MAX: специфика другой платформы
3. `platforms/base_adapter.py` — абстрактный базовый класс для всех адаптеров

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.