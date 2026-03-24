"""
SQLite хранилище прогресса пользователей.
Версия: 2.16 (Fix: Singleton connection + full restore) 🗄️✅
"""

import sqlite3
import json
import os
import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "progress.db")

# 🔥 ГЛОБАЛЬНОЕ СОЕДИНЕНИЕ (Singleton)
_connection = None


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def get_connection():
    """Возвращает ОДНО соединение на всё приложение."""
    global _connection
    
    if _connection is None:
        ensure_data_dir()
        logger.info(f"🔌 Создаём глобальное соединение с БД: {DB_FILE}")
        
        _connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        
        # ✅ OPTIMIZATIONS FOR CONCURRENCY (WAL mode)
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA synchronous=NORMAL")
        _connection.execute("PRAGMA busy_timeout=5000")
        _connection.execute("PRAGMA cache_size=-64000")
        _connection.execute("PRAGMA temp_store=MEMORY")
    
    return _connection


def get_db_path() -> str:
    ensure_data_dir()
    return os.path.abspath(DB_FILE)


class PlayerStorage:
    # ✅ JSON-поля которые хранятся как JSON в БД
    JSON_FIELDS = [
        'defeated_bosses', 'completed_zones', 'inventory', 'rewards', 
        'abilities', 'unlocked_zones', 'achievements', 'castle_decorations', 
        'artifact_upgrades', 'bank_data', 'castle_data',
        'player_profile'
    ]
    
    # ✅ Поля игрового состояния — упаковываются в JSON-колонку game_state
    GAME_STATE_FIELDS = [
        'current_level', 'current_task_index', 'mistakes_in_level',
        'in_boss_battle', 'in_secret_level', 'current_boss', 'boss_health',
        'boss_max_health', 'boss_turn', 'boss_task_index', 'just_completed_level',
        'true_lord_error_count', 'true_lord_consecutive_successes',
        'true_lord_used_hint', 'true_lord_secret_unlocked', 'selected_tasks',
        'selected_boss_tasks', 'boss_abilities_used'
    ]
    
    # ✅ Колонки в таблице БД
    DB_COLUMNS = [
        'user_id', 'username', 'first_name',
        'level', 'xp', 'xp_to_next',
        'total_score', 'score_balance', 'season_score', 'season_id',
        'tasks_solved', 'tasks_correct',
        'defeated_bosses', 'completed_zones', 'inventory', 'unlocked_zones',
        'rewards', 'abilities', 'achievements', 'castle_decorations', 'artifact_upgrades',
        'game_state', 'created_at', 'updated_at',
        'bank_data', 'castle_data', 'player_profile',
        'first_time'
    ]
    
    def __init__(self):
        # 🔥 Используем глобальное соединение
        self.conn = get_connection()
        logger.info(f"✅ PlayerStorage инициализирован (conn_id={id(self.conn)})")
        
        self._ensure_player_profile_column()
        self._ensure_first_time_column()

    def _ensure_first_time_column(self):
        """Добавляет колонку first_time если её нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
    
        if 'first_time' not in columns:
            logger.info("🔧 Добавляем колонку first_time...")
            cursor.execute("ALTER TABLE users ADD COLUMN first_time INTEGER DEFAULT 1")
            self.conn.commit()
            logger.info("✅ Колонка first_time добавлена!") 
    
    def _ensure_player_profile_column(self):
        """Добавляет колонку player_profile если её нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'player_profile' not in columns:
            logger.info("🔧 Добавляем колонку player_profile...")
            cursor.execute("ALTER TABLE users ADD COLUMN player_profile TEXT")
            self.conn.commit()
            logger.info("✅ Колонка player_profile добавлена!")
    
    def get_db_path(self) -> str:
        return get_db_path()
    
    # 🔥 ФУНКЦИЯ: извлекаем числовой user_id из строки типа "telegram_123456"
    @staticmethod
    def _extract_numeric_user_id(user_id) -> int:
        """Извлекает числовой user_id из строки формата 'platform_123456'."""
        if isinstance(user_id, int):
            return user_id
        
        user_id_str = str(user_id).strip()
        
        for prefix in ['telegram_', 'vk_', 'max_', 'web_', 'max_ru_']:
            if user_id_str.startswith(prefix):
                user_id_str = user_id_str[len(prefix):]
                break
        
        match = re.search(r'\d+', user_id_str)
        if match:
            return int(match.group())
        
        try:
            return int(user_id_str)
        except (ValueError, TypeError):
            logger.error(f"❌ Не удалось извлечь numeric user_id из: {user_id}")
            return 0
    
    def _deserialize_row(self, row: sqlite3.Row) -> Optional[Dict]:
        """Превращает строку из БД в словарь Python."""
        if not row:
            return None
        
        data = dict(row)
        
        # Десериализуем JSON-поля
        for field in self.JSON_FIELDS:
            if field in data and data[field] is not None:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = [] if field not in ['achievements', 'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile'] else {}
            elif field in data:
                data[field] = [] if field not in ['achievements', 'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile'] else {}
        
        # FIX: Десериализуем bank_data, castle_data и player_profile отдельно
        for field in ['bank_data', 'castle_data', 'player_profile']:
            if field in data:
                if data[field] is None:
                    data[field] = {}
                elif isinstance(data[field], str):
                    try:
                        data[field] = json.loads(data[field])
                    except (json.JSONDecodeError, TypeError):
                        data[field] = {}
        
        # Десериализуем game_state и "распаковываем" его в корень
        if 'game_state' in data and data['game_state']:
            try:
                game_state = json.loads(data['game_state'])
                data.update(game_state)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # ОБРАБОТКА first_time (INTEGER → boolean)
        if 'first_time' in data:
            if isinstance(data['first_time'], int):
                data['first_time'] = bool(data['first_time'])
        elif 'first_time' not in data:
            data['first_time'] = not (data.get('tasks_solved', 0) > 0 or data.get('level', 1) > 1)
        
        # Гарантируем unlocked_zones
        if not data.get('unlocked_zones'):
            data['unlocked_zones'] = ['addition']
        
        # 🔥 ГАРАНТИРУЕМ total_score и score_balance (ОБЯЗАТЕЛЬНО!)
        if data.get('total_score') is None:
            data['total_score'] = 0
        if data.get('score_balance') is None:
            data['score_balance'] = data.get('total_score', 0)
        
        # Гарантируем castle_data
        if 'castle_data' not in data:
            data['castle_data'] = {"decorations": [], "upkeep_paid_until": None}
        
        # Гарантируем player_profile
        if 'player_profile' not in data or not data['player_profile']:
            data['player_profile'] = {
                "greed": 0, "risk": 0, "logic": 0, "persistence": 0, "creativity": 0,
                "boss_stats": {"bosses_defeated": [], "attempts_per_boss": {}, "final_boss_attempts": 0, "best_accuracy": 0.0},
                "difficulty_profile": {"avg_accuracy": 0.0, "avg_response_time": 0.0, "hint_usage": 0, "streak_best": 0, "streak_current": 0},
                "secret_room": {"attempts_today": 0, "last_visit": None, "last_visit_date": None, "total_visits": 0, "streak": 0, "lore_seen": []},
                "weaknesses": {}, "strengths": {},
                "last_comment": 0, "mystery_unlocked": False, "comment_count": 0,
            }
        
        # ГАРАНТИРУЕМ ПОЛЯ ИГРОВОГО СОСТОЯНИЯ
        for field in self.GAME_STATE_FIELDS:
            if field not in data:
                if field in ['current_level', 'current_boss']:
                    data[field] = None
                elif field in ['current_task_index', 'boss_health', 'boss_turn', 'boss_task_index', 
                              'mistakes_in_level', 'true_lord_error_count', 'true_lord_consecutive_successes']:
                    data[field] = 0
                elif field in ['selected_tasks', 'selected_boss_tasks', 'boss_abilities_used']:
                    data[field] = []
                elif field in ['in_boss_battle', 'in_secret_level', 'just_completed_level', 
                              'true_lord_used_hint', 'true_lord_secret_unlocked']:
                    data[field] = False
                else:
                    data[field] = None
        
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
                    value = [] if key not in ['achievements', 'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile'] else {}
                result[key] = json.dumps(value, ensure_ascii=False) if value else None
            elif key in self.DB_COLUMNS and key not in ['game_state', 'created_at', 'user_id']:
                if key == 'first_time':
                    result[key] = 1 if value else 0
                else:
                    result[key] = value
        
        if game_state and 'game_state' in self.DB_COLUMNS:
            result['game_state'] = json.dumps(game_state, ensure_ascii=False)
        
        return result
    
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> Dict:
        # 🔍 ОТЛАДКА: покажем что приходит и что извлекаем
        user_id_int = self._extract_numeric_user_id(user_id)
        logger.info(f"🔍 get_or_create_user: input={user_id} (type={type(user_id).__name__}) -> extracted={user_id_int}")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id_int,))
        row = cursor.fetchone()
        
        if row:
            logger.info(f"✅ get_or_create_user: FOUND existing user {user_id_int}")
            data = self._deserialize_row(row)
            if username and data.get('username') != username:
                cursor.execute(
                    "UPDATE users SET username = ?, updated_at = ? WHERE user_id = ?",
                    (username, datetime.now(timezone.utc).isoformat(), user_id_int)
                )
                self.conn.commit()
            return data
        else:
            logger.info(f"🆕 get_or_create_user: CREATING new user {user_id_int}")
            default_data = {
                "user_id": user_id_int, "username": username, "first_name": first_name,
                "level": 1, "xp": 0, "xp_to_next": 50,
                "total_score": 0, "score_balance": 0, "season_score": 0, "season_id": 1,
                "tasks_solved": 0, "tasks_correct": 0,
                "unlocked_zones": ["addition"], "completed_zones": [], "defeated_bosses": [],
                "inventory": [], "rewards": [], "abilities": [],
                "achievements": {}, "castle_decorations": [], "artifact_upgrades": {},
                "bank_data": {},
                "castle_data": {"decorations": [], "upkeep_paid_until": None},
                "secret_room_level": 1,
                "secret_room_exp": 0,
                "secret_room_items": [],
                "secret_room_logs": [],
                "secret_room_last_event": None,
                "player_profile": {
                    "greed": 0, "risk": 0, "logic": 0, "persistence": 0, "creativity": 0,
                    "boss_stats": {"bosses_defeated": [], "attempts_per_boss": {}, "final_boss_attempts": 0, "best_accuracy": 0.0},
                    "difficulty_profile": {"avg_accuracy": 0.0, "avg_response_time": 0.0, "hint_usage": 0, "streak_best": 0, "streak_current": 0},
                    "secret_room": {"attempts_today": 0, "last_visit": None, "last_visit_date": None, "total_visits": 0, "streak": 0, "lore_seen": []},
                    "weaknesses": {}, "strengths": {},
                    "last_comment": 0, "mystery_unlocked": False, "comment_count": 0,
                },
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
            logger.info(f"🆕 Пользователь {user_id_int} создан (INSERT + COMMIT)")
            return default_data
    
    def save_user(self, user_id: int, data: Dict) -> bool:
        """Сохраняет данные пользователя. Возвращает True при успехе."""
        try:
            user_id_int = self._extract_numeric_user_id(user_id)
            
            cursor = self.conn.cursor()
            db_data = self._serialize_for_db(data)
            db_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            filtered = {k: v for k, v in db_data.items() if k in self.DB_COLUMNS and k != 'user_id'}
            
            sets = ', '.join([f"{k} = ?" for k in filtered.keys()])
            values = list(filtered.values()) + [user_id_int]
            
            cursor.execute(f"UPDATE users SET {sets} WHERE user_id = ?", values)
            
            # Если пользователя ещё нет в БД, создаём запись на лету.
            if cursor.rowcount == 0:
                logger.info(f"🆕 SAVE_USER: user {user_id_int} не найден, создаём запись (upsert)")
                insert_data = {'user_id': user_id_int, **filtered}
                insert_data['created_at'] = datetime.now(timezone.utc).isoformat()
                insert_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                insert_cols = [k for k in insert_data.keys() if k in self.DB_COLUMNS]
                insert_placeholders = ", ".join(["?" for _ in insert_cols])
                insert_values = [insert_data[k] for k in insert_cols]
                
                cursor.execute(
                    f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({insert_placeholders})",
                    insert_values
                )
            
            logger.info(f"💾 SAVE_USER: user_id={user_id_int}, total_score={filtered.get('total_score', 'N/A')}, score_balance={filtered.get('score_balance', 'N/A')}")
            
            if 'player_profile' in filtered:
                try:
                    pp = json.loads(filtered['player_profile'])
                    logger.info(f"💾 player_profile: attempts_today={pp['secret_room']['attempts_today']}")
                except:
                    pass
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка save_user: {e}")
            self.conn.rollback()
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        # 🔍 ОТЛАДКА: покажем что приходит и что извлекаем
        user_id_int = self._extract_numeric_user_id(user_id)
        logger.info(f"🔍 get_user: input={user_id} (type={type(user_id).__name__}) -> extracted={user_id_int}")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id_int,))
        row = cursor.fetchone()
        
        if row:
            logger.info(f"✅ get_user: FOUND user {user_id_int} in DB")
            return self._deserialize_row(row)
        else:
            logger.error(f"❌ get_user: user {user_id_int} NOT FOUND in DB!")
            return None
    
    def delete_user(self, user_id: int):
        user_id_int = self._extract_numeric_user_id(user_id)
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM score_log WHERE user_id = ?", (user_id_int,))
        cursor.execute("DELETE FROM task_history WHERE user_id = ?", (user_id_int,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id_int,))
        self.conn.commit()
        logger.info(f"🗑️ Пользователь {user_id_int} и его данные удалены")
    
    def log_score_change(self, user_id: int, amount: int, reason: str, 
                        context: str = None, season_id: int = None) -> bool:
        try:
            user_id_int = self._extract_numeric_user_id(user_id)
            
            cursor = self.conn.cursor()
            if season_id is None:
                user = self.get_user(user_id_int)
                season_id = user.get('season_id', 1) if user else 1
            
            cursor.execute("""
                INSERT INTO score_log (user_id, amount, reason, context, season_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id_int, amount, reason, context, season_id, datetime.now(timezone.utc).isoformat()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка log_score_change: {e}")
            self.conn.rollback()
            return False
    
    def get_score_history(self, user_id: int, limit: int = 50, 
                         season_id: int = None) -> List[Dict]:
        user_id_int = self._extract_numeric_user_id(user_id)
        
        cursor = self.conn.cursor()
        if season_id:
            cursor.execute("""
                SELECT * FROM score_log 
                WHERE user_id = ? AND season_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id_int, season_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM score_log 
                WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
            """, (user_id_int, limit))
        
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
        user_id_int = self._extract_numeric_user_id(user_id)
        
        user = self.get_user(user_id_int)
        if not user:
            return {}
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_earned,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_spent
            FROM score_log WHERE user_id = ?
        """, (user_id_int,))
        money_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT task_type, COUNT(*) as total, 
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM task_history WHERE user_id = ? GROUP BY task_type
        """, (user_id_int,))
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
        # 🔥 Не закрываем глобальное соединение — оно нужно всему приложению
        logger.info("✅ PlayerStorage.close() вызван (глобальное соединение не закрывается)")
        # if self.conn:
        #     self.conn.close()
        #     logger.info("✅ Соединение с БД закрыто")