# reset_level.py
"""
Сбрасывает зависший уровень
"""
import sqlite3
import json

conn = sqlite3.connect('data/progress.db')
c = conn.cursor()

c.execute('SELECT game_state FROM users WHERE user_id = 5001966771')
row = c.fetchone()

if row and row[0]:
    game_state = json.loads(row[0])
    game_state['current_level'] = None
    game_state['selected_tasks'] = []
    game_state['current_task_index'] = 0
    game_state['in_boss_battle'] = False
    
    c.execute('UPDATE users SET game_state = ? WHERE user_id = 5001966771', 
              (json.dumps(game_state),))
    conn.commit()
    print('✅ Уровень сброшен!')
else:
    print('⚠️ Данные не найдены')

conn.close()