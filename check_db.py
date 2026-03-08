# check_db.py
"""
Скрипт для проверки базы данных «Числяндия».
Запуск: python check_db.py
"""

import sqlite3
import os
import sys

# 🔧 Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "progress.db")

print(f"🔍 Проверяю базу: {DB_PATH}")
print(f"📁 Файл существует: {os.path.exists(DB_PATH)}\n")

if not os.path.exists(DB_PATH):
    print("❌ База не найдена! Запусти бота один раз, чтобы она создалась.")
    sys.exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Проверяем колонки в users
    print("📋 Колонки в таблице 'users':")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        # col = (id, name, type, notnull, default, pk)
        marker = "✨ NEW" if col[1] in ['score_balance', 'season_score', 'season_id'] else ""
        print(f"  • {col[1]:20} ({col[2]:10}) {marker}")
    
    # 2. Показываем пример данных
    print("\n💰 Пример данных (первые 3 пользователя):")
    cursor.execute("""
        SELECT user_id, username, total_score, score_balance, season_score 
        FROM users LIMIT 3
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  User {row[0]} ({row[1]}): total={row[2]}, balance={row[3]}, season={row[4]}")
    else:
        print("  (пока нет пользователей)")
    
    # 3. Проверяем score_log
    print("\n📝 Таблица 'score_log':")
    cursor.execute("SELECT COUNT(*) FROM score_log")
    count = cursor.fetchone()[0]
    print(f"  Записей: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT user_id, amount, reason, created_at 
            FROM score_log ORDER BY created_at DESC LIMIT 3
        """)
        for row in cursor.fetchall():
            print(f"  • User {row[0]}: {row[1]:+d} ({row[2]}) [{row[3]}]")
    
    # 4. Проверяем индексы
    print("\n🔎 Индексы на 'users':")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
    for idx in cursor.fetchall():
        print(f"  • {idx[0]}")
    
    conn.close()
    print("\n✅ Проверка завершена!")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()