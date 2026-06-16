# 🔧 ЭТО ДОЛЖНО БЫТЬ ПЕРВЫМ!
import sys
import os

# Добавляем корень проекта (Chislyandia/) в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 🔧 Теперь импорты сработают!
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS  # ← ДОБАВЛЯЕМ CORS!
from core.game_engine import ChislyandiaEngine
from core.score_manager import ScoreManager
from database.storage import PlayerStorage

app = Flask(
    __name__,
    template_folder=os.path.join(current_dir, 'templates'),
    static_folder=os.path.join(current_dir, 'static')
)
app.secret_key = 'chislyandia-secret-key-change-me'

# 🔧 ВКЛЮЧАЕМ CORS для локальной разработки (React на порту 5173)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

# ← ЦЕПОЧКА ЗАВИСИМОСТЕЙ (важен порядок!)
storage = PlayerStorage()  # 1. Сначала база
score_manager = ScoreManager(storage)  # 2. ScoreManager получает базу
game_engine = ChislyandiaEngine(storage, score_manager)  # 3. Ядро получает оба

# ← КЭШ для задач (чтобы не генерировать одну и ту же)
user_tasks = {}

# 🔹 ГЛАВНАЯ СТРАНИЦА (без /api префикса — для браузера)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = storage.get_user(user_id)
    if not user:
        return render_template('error.html', message='Игрок не найден'), 404
    return render_template('profile.html', user=user, user_id=user_id)

# 🔹 API ENDPOINTS (с /api префиксом — для React)

@app.route('/api/game/progress/<int:user_id>')
def api_game_progress(user_id):
    """API: Получить прогресс игрока"""
    user = storage.get_user(user_id)
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'user_id': user_id,
        'level': user.get('level', 1),
        'total_score': user.get('total_score', 0),
        'score_balance': user.get('score_balance', 0),
        'tasks_solved': user.get('tasks_solved', 0)
    })

@app.route('/api/game/answer', methods=['POST'])
def api_game_answer():
    """API: Обработать ответ на задачу"""
    data = request.get_json()
    user_id = data.get('user_id')
    answer = data.get('answer')
    task_id = data.get('task_id', 'web_task')
    expected_answer = data.get('expected_answer')
    
    if not user_id or answer is None or expected_answer is None:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    
    try:
        result = game_engine.solve_task(
            user_id=str(user_id),
            answer=int(answer),
            task_id=task_id,
            expected_answer=expected_answer
        )
        
        user = storage.get_user(str(user_id))
        
        return jsonify({
            'success': True,
            'correct': result['correct'],
            'score_change': result.get('score_earned', 0),
            'total_score': user.get('total_score', 0) if user else 0,
            'message': result.get('message', '')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/castle/<int:user_id>')
def api_castle_info(user_id):
    """API: Информация о замке"""
    info = game_engine.get_castle_info(str(user_id))
    return jsonify(info)

@app.route('/api/castle/pay', methods=['POST'])
def api_castle_pay():
    """API: Оплатить содержание замка"""
    data = request.get_json()
    user_id = data.get('user_id')
    days = data.get('days', 1)
    success, message = game_engine.pay_castle_upkeep(str(user_id), days)
    return jsonify({'success': success, 'message': message})

@app.route('/api/bank/<int:user_id>')
def api_bank_info(user_id):
    """API: Информация о банке"""
    info = game_engine.get_bank_info(str(user_id))
    return jsonify(info)

@app.route('/api/bank/deposit', methods=['POST'])
def api_bank_deposit():
    """API: Вклад в банк"""
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    success, message = game_engine.deposit_to_bank(str(user_id), amount)
    return jsonify({'success': success, 'message': message})

@app.route('/api/bank/withdraw', methods=['POST'])
def api_bank_withdraw():
    """API: Снятие из банка"""
    data = request.get_json()
    user_id = data.get('user_id')
    success, message, total = game_engine.withdraw_from_bank(str(user_id))
    return jsonify({'success': success, 'message': message, 'total': total})

# 🔹 ЗАГЛУШКА ДЛЯ ГЕНЕРАЦИИ ЗАДАЧ (пока нет полноценной логики)
@app.route('/api/game/new-task', methods=['POST'])
def api_new_task():
    """API: Сгенерировать новую задачу (заглушка)"""
    import random
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    return jsonify({
        'question': f"{a} + {b} = ?",
        'answer': a + b,
        'task_id': f"add_{a}_{b}",
        'taskType': 'addition'
    })

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса Числяндии...")
    print("📍 Frontend: http://localhost:5173")
    print("🔌 Backend API: http://localhost:5000/api")
    print("✅ CORS enabled for localhost:5173")
    app.run(host='0.0.0.0', port=5000, debug=True)