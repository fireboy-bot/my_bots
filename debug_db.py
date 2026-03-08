# debug_db.py
"""
Проверка и исправление базы данных
"""
import sqlite3
import json

conn = sqlite3.connect('data/progress.db')
c = conn.cursor()

print("=" * 60)
print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 60)

# Проверяем completed_zones
c.execute('SELECT completed_zones FROM users WHERE user_id=5001966771')
row = c.fetchone()
if row and row[0]:
    completed = json.loads(row[0])
    print(f"\n📊 completed_zones ({len(completed)} зон):")
    for zone in completed:
        print(f"   - {zone}")
    
    # Считаем только 4 основных острова
    main_zones = ["addition", "subtraction", "multiplication", "division"]
    islands_count = len([z for z in completed if z in main_zones])
    print(f"\n✅ Острова (4 основных): {islands_count}/4")
else:
    print("⚠️ completed_zones не найдены")

# Проверяем unlocked_zones
c.execute('SELECT unlocked_zones FROM users WHERE user_id=5001966771')
row = c.fetchone()
if row and row[0]:
    unlocked = json.loads(row[0])
    print(f"\n📊 unlocked_zones ({len(unlocked)} зон):")
    for zone in unlocked:
        print(f"   - {zone}")
    
    # Добавляем миры если нет
    new_zones = ['time_world', 'measure_world', 'logic_world']
    added = []
    for zone in new_zones:
        if zone not in unlocked:
            unlocked.append(zone)
            added.append(zone)
    
    if added:
        c.execute('UPDATE users SET unlocked_zones=? WHERE user_id=5001966771', 
                  (json.dumps(unlocked),))
        conn.commit()
        print(f"\n✅ ДОБАВЛЕНО миров: {added}")
    else:
        print(f"\n✅ Миры уже в базе")
else:
    print("⚠️ unlocked_zones не найдены")

print("\n" + "=" * 60)
print("🎉 ПРОВЕРКА ЗАВЕРШЕНА!")
print("=" * 60)

conn.close()