"""
Flask API сервер для Числяндия фронтенда.
WebAdapter — ПРОСТОЙ мост между React и ChislyandiaEngine.
ВСЯ логика — в ядре (core/game_engine.py). Здесь только трансляция.

Контракт: frontend/src/adapters/api.js
• Порт: 5000
• Эндпоинты: /api/game/answer, /api/game/progress/:id, etc.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import sys
import logging
import random
from datetime import datetime, timezone

# 🔹 Добавляем корень проекта в path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# 🔹 Импорт ядра (ВСЯ логика здесь)
from database.storage import PlayerStorage
from core.score_manager import ScoreManager
from core.game_engine import ChislyandiaEngine

# 🔹 Настройка логирования
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOGS_DIR, 'api_server.log'), encoding='utf-8', errors='replace')
    ]
)
logger = logging.getLogger(__name__)

# 🔹 Создаём Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})

# 🔹 Инициализация ядра (ЕДИНСТВЕННОЕ место где создаём объекты)
logger.info("[INIT] WebAdapter starting...")
storage = PlayerStorage()
score_manager = ScoreManager(storage)
engine = ChislyandiaEngine(storage, score_manager)
logger.info("[INIT] WebAdapter ready! Core initialized.")


# =============================================================================
# 🔹 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (только для загрузки задач из файла)
# =============================================================================

def _get_mock_tasks(world=None):
    """Заглушки задач — если файл не найден или пустой"""
    mock = [
        {"id": "mock_add_1", "question": "5 + 3 = ?", "options": ["6", "7", "8", "9"], 
         "correct_answer": "8", "score": 10, "world": "addition", "island": "addition", "operation_type": "2digit_add"},
        {"id": "mock_mult_1", "question": "7 × 6 = ?", "options": ["36", "42", "48", "54"], 
         "correct_answer": "42", "score": 15, "world": "multiplication", "island": "multiplication", "operation_type": "1digit_mult"},
    ]
    return [t for t in mock if not world or t.get('world') == world] if world else mock


def load_tasks_from_file(world=None):
    """
    Загружает задачи из data/tasks.json.
    Поддерживает формат: { "addition": { "tasks": [ {...} ] } }
    Возвращает список нормализованных задач.
    """
    tasks_file = os.path.join(BASE_DIR, "data", "tasks.json")
    
    if not os.path.exists(tasks_file):
        logger.warning(f"[WARN] {tasks_file} not found, using mock")
        return _get_mock_tasks(world)
    
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tasks = []
        
        # 🔹 Ожидаем: { "world_name": { "tasks": [...] } }
        if isinstance(data, dict):
            for world_name, world_data in data.items():
                if isinstance(world_data, dict) and 'tasks' in world_data:
                    raw_tasks = world_data['tasks']
                    if isinstance(raw_tasks, list):
                        for idx, task in enumerate(raw_tasks):
                            if not isinstance(task, dict):
                                continue
                            
                            # 🔹 Получаем правильный ответ
                            correct = task.get('correct_answer') or task.get('answer')
                            if correct is None:
                                continue
                            correct_str = str(correct).strip()
                            
                            # 🔹 Генерируем варианты если нет
                            options = task.get('options')
                            if not options or not isinstance(options, list):
                                try:
                                    c = int(correct_str)
                                    opts = {correct_str}
                                    for off in [-10, -5, -3, 3, 5, 10]:
                                        w = str(c + off)
                                        if w != correct_str:
                                            opts.add(w)
                                        if len(opts) >= 4:
                                            break
                                    options = list(opts)
                                    random.shuffle(options)
                                except:
                                    options = [correct_str] * 4
                            
                            # 🔹 Определяем тип операции
                            q = task.get('question', '').lower()
                            if '×' in q or '*' in q or 'умнож' in q:
                                op = '1digit_mult'
                            elif '÷' in q or '/' in q or 'дел' in q:
                                op = '2digit_div'
                            elif '-' in q or 'вычит' in q:
                                op = '2digit_sub'
                            else:
                                op = '2digit_add'
                            
                            tasks.append({
                                "id": task.get('id') or f"{world_name}_{idx}",
                                "question": task.get('question', ''),
                                "correct_answer": correct_str,
                                "options": options,
                                "score": 10,
                                "world": world_name,
                                "island": world_name,
                                "operation_type": op
                            })
        
        # 🔹 Фильтр по world
        if world:
            tasks = [t for t in tasks if t.get('world') == world or t.get('island') == world]
        
        return tasks if tasks else _get_mock_tasks(world)
        
    except Exception as e:
        logger.error(f"[ERROR] load_tasks_from_file: {e}")
        return _get_mock_tasks(world)


# =============================================================================
# 🔹 ЭНДПОИНТЫ (ПРОСТАЯ ТРАНСЛЯЦИЯ: запрос → ядро → ответ)
# =============================================================================

# 🔹 HEALTH (без изменений)
@app.route('/api/health')
def health():
    """[GET] Проверка что сервер работает"""
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "service": "chislyandia-web-adapter"})


# 🔹 ПРОФИЛЬ ИГРОКА — добавляем АЛИАС для api.js
@app.route('/api/player/<user_id>/profile')
@app.route('/api/game/progress/<user_id>')  # 🔹 АЛИАС для api.getProgress()
def get_player_profile(user_id):
    """[GET] Профиль игрока — вызываем ядро"""
    try:
        return jsonify(engine.get_player_profile(user_id))
    except Exception as e:
        logger.error(f"[ERROR] get_player_profile: {e}")
        return jsonify({"error": str(e)}), 500


# 🔹 ЗАДАЧА — без изменений
@app.route('/api/game/task')
def get_task():
    """[GET] Получить задачу — загружаем из файла или ядра"""
    try:
        user_id = request.args.get('user_id')
        world = request.args.get('world')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        tasks = load_tasks_from_file(world)
        if not tasks:
            return jsonify({"error": "No tasks available"}), 404
        
        return jsonify(random.choice(tasks))
        
    except Exception as e:
        logger.error(f"[ERROR] get_task: {e}")
        return jsonify({"error": str(e)}), 500


# 🔹 ПРОВЕРКА ОТВЕТА — добавляем АЛИАС для api.js
@app.route('/api/game/check_answer', methods=['POST'])
@app.route('/api/game/answer', methods=['POST'])  # 🔹 АЛИАС для api.submitAnswer()
def check_answer():
    """
    [POST] Проверить ответ — ВСЯ логика в engine.solve_task()
    
    Поддерживает оба эндпоинта:
    - /api/game/check_answer (оригинальный)
    - /api/game/answer (для api.js)
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        # 🔹 Извлекаем поля
        user_id = data.get('user_id')
        answer = data.get('answer')
        task_id = data.get('task_id')
        expected_answer = data.get('expected_answer')
        island_id = data.get('island_id')
        operation_type = data.get('operation_type')
        
        # 🔹 Валидация
        if not all([user_id, answer is not None, task_id, expected_answer is not None]):
            return jsonify({"error": "Missing required fields: user_id, answer, task_id, expected_answer"}), 400
        
        # 🔹 Приводим к строке для надёжного сравнения (solve_task делает str() внутри)
        answer_str = str(answer).strip().replace(',', '.')
        expected_str = str(expected_answer).strip().replace(',', '.')
        
        # 🔹 ВЫЗЫВАЕМ ЯДРО — вся логика там!
        result = engine.solve_task(
            user_id=str(user_id),
            answer=answer_str,
            task_id=str(task_id),
            expected_answer=expected_str,
            island_id=island_id,
            operation_type=operation_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[ERROR] check_answer: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# 🔹 БАНК — без изменений
@app.route('/api/bank/<user_id>')
def get_bank_info(user_id):
    """[GET] Информация о банке — вызываем ядро"""
    try:
        return jsonify(engine.get_bank_info(user_id))
    except Exception as e:
        logger.error(f"[ERROR] get_bank_info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/bank/<user_id>/deposit', methods=['POST'])
def deposit_to_bank(user_id):
    """[POST] Положить в банк — вызываем ядро"""
    try:
        amount = (request.get_json(silent=True) or {}).get('amount', 0)
        success, message = engine.deposit_to_bank(user_id, amount)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"[ERROR] deposit_to_bank: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/bank/<user_id>/withdraw', methods=['POST'])
def withdraw_from_bank(user_id):
    """[POST] Забрать из банка — вызываем ядро"""
    try:
        success, message, total = engine.withdraw_from_bank(user_id)
        return jsonify({"success": success, "message": message, "total": total})
    except Exception as e:
        logger.error(f"[ERROR] withdraw_from_bank: {e}")
        return jsonify({"error": str(e)}), 500


# 🔹 ЗАМОК — без изменений
@app.route('/api/castle/<user_id>')
def get_castle_info(user_id):
    """[GET] Информация о замке — вызываем ядро"""
    try:
        return jsonify(engine.get_castle_info(user_id))
    except Exception as e:
        logger.error(f"[ERROR] get_castle_info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/castle/<user_id>/upkeep', methods=['POST'])
def pay_castle_upkeep(user_id):
    """[POST] Оплатить замок — вызываем ядро"""
    try:
        days = (request.get_json(silent=True) or {}).get('days', 1)
        success, message = engine.pay_castle_upkeep(user_id, days)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"[ERROR] pay_castle_upkeep: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/castle/<user_id>/upgrade_decoration', methods=['POST'])
def upgrade_castle_decoration(user_id):
    """[POST] Улучшить декорацию — вызываем ядро"""
    try:
        dec_id = (request.get_json(silent=True) or {}).get('decoration_id')
        if not dec_id:
            return jsonify({"success": False, "message": "decoration_id required"}), 400
        
        success, message = engine.castle.upgrade_decoration(user_id, dec_id)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"[ERROR] upgrade_decoration: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# 🔹 АРТЕФАКТЫ — без изменений
@app.route('/api/artifacts/<user_id>')
def get_artifacts(user_id):
    """[GET] Артефакты — вызываем ядро"""
    try:
        return jsonify(engine.get_artifact_info(user_id))
    except Exception as e:
        logger.error(f"[ERROR] get_artifacts: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/artifacts/<user_id>/upgrade', methods=['POST'])
def upgrade_artifact(user_id):
    """[POST] Улучшить артефакт — вызываем ядро"""
    try:
        art_id = (request.get_json(silent=True) or {}).get('artifact_id')
        if not art_id:
            return jsonify({"success": False, "message": "artifact_id required"}), 400
        
        success, message = engine.upgrade_artifact(user_id, art_id)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"[ERROR] upgrade_artifact: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# =============================================================================
# 🔹 ЗАПУСК
# =============================================================================
if __name__ == '__main__':
    # 🔹 Порт 5000 — чтобы совпадал с api.js
    port = int(os.getenv('WEB_API_PORT', 5000))
    logger.info(f"[START] WebAdapter on http://127.0.0.1:{port}")
    logger.info(f"[PATH] BASE_DIR: {BASE_DIR}")
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)