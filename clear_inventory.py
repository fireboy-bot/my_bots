# clear_inventory.py
"""
Очищает инвентарь конкретного пользователя для тестов.
Запуск: py clear_inventory.py
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "progress.db")

# 🔧 ТВОЙ USER_ID (из check_db.py)
USER_ID = 5001966771

print(f"🔧 Очищаю инвентарь для пользователя {USER_ID}...\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Проверяем текущий инвентарь
cursor.execute("SELECT inventory, score_balance, total_score FROM users WHERE user_id = ?", (USER_ID,))
row = cursor.fetchone()

if row:
    inventory = row[0]
    balance = row[1]
    total = row[2]
    
    print(f"📦 Текущий инвентарь: {inventory}")
    print(f"💰 Баланс: {balance}")
    print(f"🏆 Рейтинг: {total}\n")
    
    # Очищаем инвентарь
    cursor.execute("UPDATE users SET inventory = '[]' WHERE user_id = ?", (USER_ID,))
    conn.commit()
    
    print(f"✅ Инвентарь очищен!")
    print(f"💡 Теперь можно тестировать покупки заново.\n")
else:
    print(f"❌ Пользователь {USER_ID} не найден!")

conn.close()