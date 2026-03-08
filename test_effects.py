# test_effects.py
"""
Проверка эффектов предметов
"""
import sqlite3
import json

conn = sqlite3.connect('data/progress.db')
c = conn.cursor()

c.execute('SELECT inventory, unlocked_zones FROM users WHERE user_id=5001966771')
row = c.fetchone()

if row:
    inventory = json.loads(row[0]) if row[0] else []
    unlocked = json.loads(row[1]) if row[1] else []
    
    print("=" * 60)
    print("📦 ИНВЕНТАРЬ")
    print("=" * 60)
    
    for item in inventory:
        print(f"• {item}")
    
    print("\n" + "=" * 60)
    print("🔓 РАЗБЛОКИРОВКИ")
    print("=" * 60)
    print(f"• unlocked_zones: {unlocked}")
    print(f"• completed_normal_game: {'✅' if 'final_boss' in str(unlocked) else '❌'}")
    
    print("\n" + "=" * 60)
    print("🎯 ЭФФЕКТЫ")
    print("=" * 60)
    
    # Проверяем какие эффекты должны работать
    if "gloves_sum" in inventory or "sum_gloves" in inventory:
        print("✅ Перчатки Сложения: +3 очка за задачу на сложение")
    if "potion_luck" in inventory:
        print("✅ Зелье Удачи: активный эффект")
    if "crown_mathmage" in inventory or "корона_матемага" in inventory:
        print("✅ Корона Матемага: все эффекты включены")
    if "bravery_potion" in inventory:
        print("✅ Зелье Храбрости: риск-награда")
    if "chaos_cup" in inventory:
        print("✅ Кубок Хаоса: случайные эффекты")
    if "dice_of_fate" in inventory:
        print("✅ Кубик Судьбы: бросок перед задачей")
    
    print("\n" + "=" * 60)

conn.close()