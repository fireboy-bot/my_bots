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
# 🔹 ЭНДПОИНТЫ — только прокси к ядру
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


# 🔹 МИРЫ / ОСТРОВА
@app.route('/api/game/worlds/<user_id>')
def get_worlds(user_id):
    """[GET] Каталог миров — ядро progression."""
    try:
        result = engine.get_worlds(user_id)
        if result.get("error"):
            return jsonify(result), 404
        return jsonify(result)
    except Exception as e:
        logger.error(f"[ERROR] get_worlds: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/game/level/start', methods=['POST'])
def start_level():
    """[POST] Старт забега по острову — 10 задач как в Telegram."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_id = data.get('user_id')
        world = data.get('world')

        if not user_id or not world:
            return jsonify({"error": "user_id and world required"}), 400

        result = engine.start_level_run(str(user_id), str(world))
        if result.get("error"):
            status = 404 if result["error"] == "Игрок не найден" else 403
            return jsonify(result), status
        return jsonify(result)
    except Exception as e:
        logger.error(f"[ERROR] start_level: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/game/boss/start', methods=['POST'])
def start_boss():
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_id = data.get('user_id')
        boss_id = data.get('boss_id')

        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        result = engine.start_boss_run(str(user_id), str(boss_id) if boss_id else None)
        if result.get("error"):
            status = 404 if result["error"] == "Игрок не найден" else 403
            return jsonify(result), status
        return jsonify(result)
    except Exception as e:
        logger.error(f"[ERROR] start_boss: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/game/boss/state/<user_id>')
def boss_state(user_id):
    try:
        return jsonify(engine.get_boss_state(user_id))
    except Exception as e:
        logger.error(f"[ERROR] boss_state: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/game/boss/exit', methods=['POST'])
def exit_boss():
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        return jsonify(engine.exit_boss_run(str(user_id)))
    except Exception as e:
        logger.error(f"[ERROR] exit_boss: {e}")
        return jsonify({"error": str(e)}), 500


# 🔹 ЗАДАЧА — без изменений
@app.route('/api/game/task')
def get_task():
    """[GET] Задача — ядро читает data/worlds/ (как Telegram)."""
    try:
        user_id = request.args.get('user_id')
        world = request.args.get('world')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        task = engine.get_random_task(user_id, world)
        if not task:
            if world:
                return jsonify({"error": "World locked or not found"}), 403
            return jsonify({"error": "No tasks available"}), 404
        
        return jsonify(task)
        
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
        is_transfer = bool(data.get('is_transfer', False))
        
        # 🔹 Валидация
        if not all([user_id, answer is not None, task_id]):
            return jsonify({"error": "Missing required fields: user_id, answer, task_id"}), 400
        
        # 🔹 Правильный ответ — из tasks.json по task_id (не доверяем фронту)
        resolved_expected = engine.resolve_task_answer(task_id, island_id, expected_answer)
        if resolved_expected is None:
            return jsonify({"error": "Could not resolve expected answer for task"}), 400
        
        # 🔹 Приводим ответ игрока к строке
        answer_str = str(answer).strip().replace(',', '.')
        
        # 🔹 ВЫЗЫВАЕМ ЯДРО — вся логика там!
        result = engine.solve_task(
            user_id=str(user_id),
            answer=answer_str,
            task_id=str(task_id),
            expected_answer=resolved_expected,
            island_id=island_id,
            operation_type=operation_type,
            is_transfer=is_transfer
        )
        
        logger.info(
            f"[ANSWER] user={user_id} task={task_id} given={answer_str} "
            f"expected={resolved_expected} correct={result.get('correct')}"
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


# 🔹 АЛХИМИЯ — прокси к ядру (handlers/alchemy.py)
@app.route('/api/alchemy/<user_id>/craft', methods=['POST'])
def craft_alchemy(user_id):
    """[POST] Создать зелье/артефакт в Лавке Безумца"""
    try:
        item_id = (request.get_json(force=True, silent=True) or {}).get('item_id')
        if not item_id:
            return jsonify({"success": False, "message": "item_id required"}), 400

        result = engine.craft_alchemy(str(user_id), str(item_id))
        logger.info(f"[ALCHEMY] user={user_id} item={item_id} success={result.get('success')}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"[ERROR] craft_alchemy: {e}", exc_info=True)
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