# migrate_db.py
"""
Безопасная миграция базы данных для Числяндии v2.0
Запуск: py migrate_db.py

Что делает:
- Создаёт бэкап
- Добавляет новые колонки (не удаляя старые!)
- Копирует total_score → score_balance
- Создаёт таблицу score_log
- Сохраняет ВСЕХ пользователей
"""
import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = 'data/progress.db'
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
BACKUP_PATH = f'data/progress_backup_{TIMESTAMP}.db'

print("🔧 МИГРАЦИЯ БАЗЫ ДАННЫХ v2.0\n")
print("=" * 50)

# ============================================================
# ШАГ 1: Бэкап
# ============================================================
if os.path.exists(DB_PATH):
    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f"✅ Бэкап создан: {BACKUP_PATH}")
else:
    print("⚠️  БД не найдена, будет создана новая")

# ============================================================
# ШАГ 2: Подключаемся и проверяем текущие колонки
# ============================================================
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
existing_columns = [col[1] for col in cursor.fetchall()]
print(f"\n📋 Найдено колонок в users: {len(existing_columns)}")

# ============================================================
# ШАГ 3: Добавляем новые колонки (если нет)
# ============================================================
new_columns = [
    ("first_name", "TEXT"),
    ("xp_to_next", "INTEGER DEFAULT 50"),
    ("score_balance", "INTEGER DEFAULT 0"),
    ("season_score", "INTEGER DEFAULT 0"),
    ("season_id", "INTEGER DEFAULT 1"),
    ("rewards", "TEXT DEFAULT '[]'"),
    ("abilities", "TEXT DEFAULT '[]'"),
    ("achievements", "TEXT DEFAULT '{}'"),
    ("castle_decorations", "TEXT DEFAULT '[]'"),
    ("artifact_upgrades", "TEXT DEFAULT '{}'"),
]

print("\n➕ Добавляем новые колонки:")
for col_name, col_type in new_columns:
    if col_name not in existing_columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"   ✅ {col_name}")
        except Exception as e:
            print(f"   ⚠️  {col_name} (ошибка: {e})")
    else:
        print(f"   ✓  {col_name} (уже есть)")

# ============================================================
# ШАГ 4: Копируем total_score → score_balance
# ============================================================
print("\n💰 Копируем очки в баланс...")
cursor.execute("""
    UPDATE users 
    SET score_balance = total_score 
    WHERE score_balance IS NULL OR score_balance = 0
""")
print(f"   ✅ Обновлено строк: {cursor.rowcount}")

# ============================================================
# ШАГ 5: Создаём таблицу score_log
# ============================================================
print("\n📝 Проверяем таблицу score_log...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score_log'")
if not cursor.fetchone():
    cursor.execute("""
        CREATE TABLE score_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,
            context TEXT,
            season_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    print("   ✅ Таблица score_log создана")
else:
    print("   ✓  score_log уже есть")

# ============================================================
# ШАГ 6: Создаём таблицу task_history (если нет)
# ============================================================
print("\n📝 Проверяем таблицу task_history...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_history'")
if not cursor.fetchone():
    cursor.execute("""
        CREATE TABLE task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_type TEXT,
            difficulty TEXT,
            is_correct INTEGER,
            time_spent REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    print("   ✅ Таблица task_history создана")
else:
    print("   ✓  task_history уже есть")

# ============================================================
# ШАГ 7: Сохраняем и закрываем
# ============================================================
conn.commit()

# Проверяем итог
cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]
print(f"\n👥 Всего пользователей: {user_count}")

conn.close()

print("\n" + "=" * 50)
print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА!")
print("=" * 50)
print("\n🚀 Следующий шаг: запусти py check_db.py для проверки")