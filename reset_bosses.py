# reset_bosses.py
"""
Сбрасывает список побеждённых боссов
"""
import sqlite3
import json

conn = sqlite3.connect('data/progress.db')
c = conn.cursor()

c.execute('SELECT defeated_bosses FROM users WHERE user_id = 5001966771')
row = c.fetchone()

if row and row[0]:
    defeated = json.loads(row[0])
    print(f"📊 Было: defeated_bosses = {defeated}")
    
    c.execute('UPDATE users SET defeated_bosses = ? WHERE user_id = 5001966771', 
              (json.dumps([]),))
    conn.commit()
    print("✅ defeated_bosses очищен!")
else:
    print("⚠️ Данные не найдены")

conn.close()
print("🎉 Готово!")