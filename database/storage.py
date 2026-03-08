"""
SQLite хранилище прогресса пользователей.
Версия: 2.4 (Fix: bank_data deserialization) 🗄️✅
"""

import sqlite3
import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "progress.db")


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def get_connection():
    ensure_data_dir()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # ✅ OPTIMIZATIONS FOR CONCURRENCY (WAL mode)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA temp_store=MEMORY")
    
    return conn


def get_db_path() -> str:
    ensure_data_dir()
    return os.path.abspath(DB_FILE)


class PlayerStorage:
    JSON_FIELDS = [
        'defeated_bosses', 'completed_zones', 'inventory', 'rewards', 
        'abilities', 'unlocked_zones', 'achievements', 'castle_decorations', 
        'artifact_upgrades', 'bank_data'
    ]
    
    GAME_STATE_FIELDS = [
        'current_level', 'current_task_index', 'mistakes_in_level',
        'in_boss_battle', 'in_secret_level', 'current_boss', 'boss_health',
        'boss_max_health', 'boss_turn', 'boss_task_index', 'just_completed_level',
        'true_lord_error_count', 'true_lord_consecutive_successes',
        'true_lord_used_hint', 'true_lord_secret_unlocked', 'selected_tasks',
        'selected_boss_tasks', 'boss_abilities_used'
    ]
    
    DB_COLUMNS = [
        'user_id', 'username', 'first_name',
        'level', 'xp', 'xp_to_next',
        'total_score', 'score_balance', 'season_score', 'season_id',
        'tasks_solved', 'tasks_correct',
        'defeated_bosses', 'completed_zones', 'inventory', 'unlocked_zones',
        'rewards', 'abilities', 'achievements', 'castle_decorations', 'artifact_upgrades',
        'game_state', 'created_at', 'updated_at',
        'bank_data'
    ]
    
    def __init__(self):
        self.conn = get_connection()
        logger.info(f"✅ PlayerStorage инициализирован: {DB_FILE}")
    
    def get_db_path(self) -> str:
        return get_db_path()
    
    def _deserialize_row(self, row: sqlite3.Row) -> Optional[Dict]:
        """Превращает строку из БД в словарь Python."""
        if not row:
            return None
        
        data = dict(row)
        
        # Десериализуем JSON-поля
        for field in self.JSON_FIELDS:
            if field in data and data[field] is not None:  # ✅ FIX: проверяем на None, а не на truthiness
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = [] if field not in ['achievements', 'artifact_upgrades', 'bank_data'] else {}
            elif field in data:
                data[field] = [] if field not in ['achievements', 'artifact_upgrades', 'bank_data'] else {}
        
        # ✅ FIX: Десериализуем bank_data отдельно с правильной проверкой
        if 'bank_data' in data:
            if data['bank_data'] is None:
                data['bank_data'] = {}
            elif isinstance(data['bank_data'], str):
                try:
                    data['bank_data'] = json.loads(data['bank_data'])
                except (json.JSONDecodeError, TypeError):
                    data['bank_data'] = {}
        
        # Десериализуем game_state и "распаковываем" его в корень
        if 'game_state' in data and data['game_state']:
            try:
                game_state = json.loads(data['game_state'])
                data.update(game_state)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Гарантируем first_time для старых пользователей
        if 'first_time' not in data:
            data['first_time'] = not (data.get('tasks_solved', 0) > 0 or data.get('level', 1) > 1)
        
        # Гарантируем unlocked_zones
        if not data.get('unlocked_zones'):
            data['unlocked_zones'] = ['addition']
            
        # Гарантируем score_balance (если колонка была добавлена, но пустая)
        if data.get('score_balance') is None:
            data['score_balance'] = data.get('total_score', 0)
        
        return data
    
    def _serialize_for_db(self, data: Dict) -> Dict:
        """Подготавливает данные для записи в БД."""
        result = {}
        game_state = {}
        
        for key, value in data.items():
            if key in self.GAME_STATE_FIELDS:
                game_state[key] = value
            elif key in self.JSON_FIELDS and key in self.DB_COLUMNS:
                if value is None:
                    value = [] if key not in ['achievements', 'artifact_upgrades', 'bank_data'] else {}
                result[key] = json.dumps(value, ensure_ascii=False) if value else None
            elif key in self.DB_COLUMNS and key not in ['game_state', 'created_at', 'user_id']:
                result[key] = value
        
        # Упаковываем game_state обратно в JSON
        if game_state and 'game_state' in self.DB_COLUMNS:
            result['game_state'] = json.dumps(game_state, ensure_ascii=False)
        
        return result
    
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            data = self._deserialize_row(row)
            if username and data.get('username') != username:
                cursor.execute(
                    "UPDATE users SET username = ?, updated_at = ? WHERE user_id = ?",
                    (username, datetime.now(timezone.utc).isoformat(), user_id)
                )
                self.conn.commit()
            return data
        else:
            default_data = {
                "user_id": user_id, "username": username, "first_name": first_name,
                "level": 1, "xp": 0, "xp_to_next": 50,
                "total_score": 0, "score_balance": 0, "season_score": 0, "season_id": 1,
                "tasks_solved": 0, "tasks_correct": 0,
                "unlocked_zones": ["addition"], "completed_zones": [], "defeated_bosses": [],
                "inventory": [], "rewards": [], "abilities": [],
                "achievements": {}, "castle_decorations": [], "artifact_upgrades": {},
                "bank_data": {},  # ✅ НОВОЕ: для Златочёта
                "in_boss_battle": False, "current_boss": None, "current_level": None,
                "selected_tasks": [], "current_task_index": 0, "first_time": True,
                "completed_normal_game": False, "soul_shards": 0, "absolute_victory": False
            }
            db_data = self._serialize_for_db(default_data)
            db_data['created_at'] = datetime.now(timezone.utc).isoformat()
            db_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            columns = [k for k in db_data.keys() if k in self.DB_COLUMNS]
            placeholders = ', '.join(['?' for _ in columns])
            values = [db_data[k] for k in columns]
            
            cursor.execute(f"INSERT INTO users ({', '.join(columns)}) VALUES ({placeholders})", values)
            self.conn.commit()
            logger.info(f"🆕 Пользователь {user_id} создан")
            return default_data
    
    def save_user(self, user_id: int, data: Dict) -> bool:
        """Сохраняет данные пользователя. Возвращает True при успехе."""
        try:
            cursor = self.conn.cursor()
            db_data = self._serialize_for_db(data)
            db_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Только существующие колонки
            filtered = {k: v for k, v in db_data.items() if k in self.DB_COLUMNS and k != 'user_id'}
            
            sets = ', '.join([f"{k} = ?" for k in filtered.keys()])
            values = list(filtered.values()) + [user_id]
            
            cursor.execute(f"UPDATE users SET {sets} WHERE user_id = ?", values)
            
            # ✅ ЛОГИРОВАНИЕ ПЕРЕД COMMIT
            logger.info(f"💾 SAVE_USER: user_id={user_id}, total_score={filtered.get('total_score', 'N/A')}, score_balance={filtered.get('score_balance', 'N/A')}")
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка save_user: {e}")
            self.conn.rollback()
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return self._deserialize_row(row) if row else None
    
    def delete_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM score_log WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM task_history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.conn.commit()
        logger.info(f"🗑️ Пользователь {user_id} и его данные удалены")
    
    def log_score_change(self, user_id: int, amount: int, reason: str, 
                        context: str = None, season_id: int = None) -> bool:
        try:
            cursor = self.conn.cursor()
            if season_id is None:
                user = self.get_user(user_id)
                season_id = user.get('season_id', 1) if user else 1
            
            cursor.execute("""
                INSERT INTO score_log (user_id, amount, reason, context, season_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, reason, context, season_id, datetime.now(timezone.utc).isoformat()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка log_score_change: {e}")
            self.conn.rollback()
            return False
    
    def get_score_history(self, user_id: int, limit: int = 50, 
                         season_id: int = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if season_id:
            cursor.execute("""
                SELECT * FROM score_log 
                WHERE user_id = ? AND season_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, season_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM score_log 
                WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_leaderboard(self, period: str = 'all', limit: int = 10, 
                       season_id: int = None) -> List[Dict]:
        cursor = self.conn.cursor()
        
        if period == 'all':
            cursor.execute("""
                SELECT user_id, username, total_score, level 
                FROM users ORDER BY total_score DESC LIMIT ?
            """, (limit,))
        else:
            time_filter = ""
            if period == 'week':
                time_filter = "AND created_at >= datetime('now', '-7 days')"
            elif period == 'month':
                time_filter = "AND created_at >= datetime('now', '-30 days')"
            elif period == 'season' and season_id:
                time_filter = f"AND season_id = {season_id}"
            
            cursor.execute(f"""
                SELECT 
                    u.user_id, u.username, u.level,
                    COALESCE(SUM(CASE WHEN sl.amount > 0 THEN sl.amount ELSE 0 END), 0) as earned,
                    COALESCE(SUM(CASE WHEN sl.amount < 0 THEN ABS(sl.amount) ELSE 0 END), 0) as spent,
                    COALESCE(SUM(sl.amount), 0) as net_score
                FROM users u
                LEFT JOIN score_log sl ON u.user_id = sl.user_id {time_filter}
                GROUP BY u.user_id
                ORDER BY net_score DESC LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_users(self) -> List[int]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row['user_id'] for row in cursor.fetchall()]
    
    def get_stats(self, user_id: int) -> Dict:
        user = self.get_user(user_id)
        if not user:
            return {}
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_earned,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_spent
            FROM score_log WHERE user_id = ?
        """, (user_id,))
        money_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT task_type, COUNT(*) as total, 
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM task_history WHERE user_id = ? GROUP BY task_type
        """, (user_id,))
        task_stats = {row['task_type']: {
            'total': row['total'],
            'correct': row['correct'],
            'accuracy': round(row['correct'] / row['total'] * 100, 1) if row['total'] > 0 else 0
        } for row in cursor.fetchall()}
        
        return {
            'user': user,
            'money': {
                'earned': money_stats['total_earned'] or 0,
                'spent': money_stats['total_spent'] or 0
            },
            'tasks': task_stats
        }
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("✅ Соединение с БД закрыто")