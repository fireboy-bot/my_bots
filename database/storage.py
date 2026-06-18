"""
SQLite хранилище прогресса пользователей.
Версия: 2.17 (Chaos hooks + Subscription hooks + Security) 🗄️🔐✅
"""

import sqlite3
import json
import os
import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# 🔐 Шифрование для родительских данных (152-ФЗ)
try:
    from cryptography.fernet import Fernet
    from config import PARENT_DATA_KEY
    _fernet = Fernet(PARENT_DATA_KEY.encode()) if PARENT_DATA_KEY else None
except ImportError:
    _fernet = None
    logging.warning("⚠️ cryptography not installed — parent_email will not be encrypted")

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


# 🔐 Функции шифрования для родительских данных
def _encrypt_parent_data(data: str) -> str:
    """Шифрует данные родителя (email, предпочтения)"""
    if not data or not _fernet:
        return data
    return _fernet.encrypt(data.encode()).decode()


def _decrypt_parent_data(encrypted: str) -> str:
    """Расшифровывает данные родителя"""
    if not encrypted or not _fernet:
        return encrypted
    return _fernet.decrypt(encrypted.encode()).decode()


class PlayerStorage:
    # ✅ JSON-поля которые хранятся как JSON в БД
    JSON_FIELDS = [
        'defeated_bosses', 'completed_zones', 'inventory', 'rewards', 
        'abilities', 'unlocked_zones', 'achievements', 'castle_decorations', 
        'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile',
        'weak_areas', 'report_preferences'  # 🔹 Новые для статистики
    ]
    
    # ✅ Поля игрового состояния — упаковываются в JSON-колонку game_state
    GAME_STATE_FIELDS = [
        'current_level', 'current_task_index', 'mistakes_in_level',
        'in_boss_battle', 'in_secret_level', 'current_boss', 'boss_health',
        'boss_max_health', 'boss_turn', 'boss_task_index', 'just_completed_level',
        'true_lord_error_count', 'true_lord_consecutive_successes',
        'true_lord_used_hint', 'true_lord_secret_unlocked', 'true_lord_epic',
        'completed_normal_game', 'absolute_victory',
        'selected_tasks',
        'selected_boss_tasks', 'boss_abilities_used',
        # 🔹 Chaos System поля (в game_state для быстрой сериализации)
        'consecutive_errors', 'chaos_energy', 'rift_stage', 'artifact_chaos_state',
        'transfer_tasks_completed'
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
        'first_time',
        # 🔹 CHAOS SYSTEM (отдельные колонки для быстрого доступа)
        'consecutive_errors', 'chaos_energy', 'rift_stage', 'artifact_chaos_state',
        'transfer_tasks_completed',
        # 🔹 DYNAMIC DIFFICULTY (будущее)
        'difficulty_level_addition', 'difficulty_level_subtraction',
        'difficulty_level_multiplication', 'difficulty_level_division',
        'tasks_on_current_level', 'accuracy_last_10',
        # 🔹 MONETIZATION / PARENT STATS (будущее)
        'parent_email', 'subscription_tier', 'report_preferences',
        'weak_areas', 'preferred_practice_time',
        # 🔹 GENERAL STATS
        'total_tasks_attempted', 'total_tasks_correct', 'accuracy_overall',
        'last_session_end'
    ]
    
    def __init__(self):
        # 🔥 Используем глобальное соединение
        self.conn = get_connection()
        logger.info(f"✅ PlayerStorage инициализирован (conn_id={id(self.conn)})")
        
        self._ensure_player_profile_column()
        self._ensure_castle_data_column()
        self._ensure_first_time_column()
        self._ensure_chaos_columns()
        self._ensure_difficulty_columns()
        self._ensure_monetization_columns()
        self._ensure_stats_columns()
        self._ensure_task_attempts_table()
        self._ensure_subscriptions_table()

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
    
    def _ensure_castle_data_column(self):
        """Добавляет колонку castle_data если её нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'castle_data' not in columns:
            logger.info("🔧 Добавляем колонку castle_data...")
            cursor.execute("ALTER TABLE users ADD COLUMN castle_data TEXT DEFAULT '{}'")
            self.conn.commit()
            logger.info("✅ Колонка castle_data добавлена!")
    
    # 🔹 НОВЫЕ МЕТОДЫ: добавляем "крючки" для будущего
    
    def _ensure_chaos_columns(self):
        """Добавляет колонки Chaos System если их нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        chaos_cols = [
            ('consecutive_errors', 'INTEGER DEFAULT 0'),
            ('chaos_energy', 'INTEGER DEFAULT 0'),
            ('rift_stage', 'INTEGER DEFAULT 0'),
            ('artifact_chaos_state', 'TEXT DEFAULT "dormant"'),
            ('transfer_tasks_completed', 'INTEGER DEFAULT 0')
        ]
        
        for col_name, col_def in chaos_cols:
            if col_name not in columns:
                logger.info(f"🔧 Добавляем колонку {col_name}...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                self.conn.commit()
                logger.info(f"✅ Колонка {col_name} добавлена!")
    
    def _ensure_difficulty_columns(self):
        """Добавляет колонки динамической сложности если их нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        diff_cols = [
            ('difficulty_level_addition', 'INTEGER DEFAULT 1'),
            ('difficulty_level_subtraction', 'INTEGER DEFAULT 1'),
            ('difficulty_level_multiplication', 'INTEGER DEFAULT 1'),
            ('difficulty_level_division', 'INTEGER DEFAULT 1'),
            ('tasks_on_current_level', 'INTEGER DEFAULT 0'),
            ('accuracy_last_10', 'REAL DEFAULT 1.0')
        ]
        
        for col_name, col_def in diff_cols:
            if col_name not in columns:
                logger.info(f"🔧 Добавляем колонку {col_name}...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                self.conn.commit()
                logger.info(f"✅ Колонка {col_name} добавлена!")
    
    def _ensure_monetization_columns(self):
        """Добавляет колонки монетизации/статистики если их нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        monet_cols = [
            ('parent_email', 'TEXT'),  # 🔐 Шифровать при сохранении!
            ('subscription_tier', 'TEXT DEFAULT "free"'),
            ('report_preferences', 'TEXT'),  # JSON
            ('weak_areas', 'TEXT'),  # JSON
            ('preferred_practice_time', 'TEXT DEFAULT "any"')
        ]
        
        for col_name, col_def in monet_cols:
            if col_name not in columns:
                logger.info(f"🔧 Добавляем колонку {col_name}...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                self.conn.commit()
                logger.info(f"✅ Колонка {col_name} добавлена!")
    
    def _ensure_stats_columns(self):
        """Добавляет общие статистические колонки если их нет."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        stats_cols = [
            ('total_tasks_attempted', 'INTEGER DEFAULT 0'),
            ('total_tasks_correct', 'INTEGER DEFAULT 0'),
            ('accuracy_overall', 'REAL DEFAULT 1.0'),
            ('last_session_end', 'DATETIME')
        ]
        
        for col_name, col_def in stats_cols:
            if col_name not in columns:
                logger.info(f"🔧 Добавляем колонку {col_name}...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                self.conn.commit()
                logger.info(f"✅ Колонка {col_name} добавлена!")
    
    def _ensure_task_attempts_table(self):
        """Создаёт таблицу task_attempts если её нет."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                island_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                time_taken_seconds REAL,
                answer_given TEXT,
                expected_answer TEXT,
                chaos_energy INTEGER DEFAULT 0,
                rift_stage INTEGER DEFAULT 0,
                transfer_task_used BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_attempts_user ON task_attempts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_attempts_time ON task_attempts(timestamp)")
        self.conn.commit()
        logger.info("✅ Таблица task_attempts готова")
    
    def _ensure_subscriptions_table(self):
        """Создаёт таблицу subscriptions если её нет."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                parent_email TEXT,
                subscription_status TEXT DEFAULT 'free',
                subscription_start DATETIME,
                subscription_end DATETIME,
                report_frequency TEXT DEFAULT 'weekly',
                weak_areas_focus TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.conn.commit()
        logger.info("✅ Таблица subscriptions готова")
    
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
                    data[field] = [] if field not in ['achievements', 'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile', 'weak_areas', 'report_preferences'] else {}
            elif field in data:
                data[field] = [] if field not in ['achievements', 'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile', 'weak_areas', 'report_preferences'] else {}
        
        # 🔐 Расшифровываем parent_email при чтении
        if 'parent_email' in data and data['parent_email']:
            try:
                data['parent_email'] = _decrypt_parent_data(data['parent_email'])
            except Exception as e:
                logger.warning(f"⚠️ Не удалось расшифровать parent_email: {e}")
                data['parent_email'] = None
        
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
        
        # 🔹 Гарантируем новые поля
        for field in ['consecutive_errors', 'chaos_energy', 'rift_stage', 'transfer_tasks_completed']:
            if field not in data or data[field] is None:
                data[field] = 0 if field != 'artifact_chaos_state' else 'dormant'
        
        for field in ['difficulty_level_addition', 'difficulty_level_subtraction', 'difficulty_level_multiplication', 'difficulty_level_division']:
            if field not in data or data[field] is None:
                data[field] = 1
        
        if 'tasks_on_current_level' not in data or data['tasks_on_current_level'] is None:
            data['tasks_on_current_level'] = 0
        if 'accuracy_last_10' not in data or data['accuracy_last_10'] is None:
            data['accuracy_last_10'] = 1.0
        
        if 'subscription_tier' not in data or data['subscription_tier'] is None:
            data['subscription_tier'] = 'free'
        if 'preferred_practice_time' not in data or data['preferred_practice_time'] is None:
            data['preferred_practice_time'] = 'any'
        
        if 'total_tasks_attempted' not in data or data['total_tasks_attempted'] is None:
            data['total_tasks_attempted'] = 0
        if 'total_tasks_correct' not in data or data['total_tasks_correct'] is None:
            data['total_tasks_correct'] = 0
        if 'accuracy_overall' not in data or data['accuracy_overall'] is None:
            data['accuracy_overall'] = 1.0
        
        # Гарантируем GAME_STATE_FIELDS
        for field in self.GAME_STATE_FIELDS:
            if field not in data:
                if field in ['current_level', 'current_boss']:
                    data[field] = None
                elif field in ['current_task_index', 'boss_health', 'boss_turn', 'boss_task_index', 
                              'mistakes_in_level', 'true_lord_error_count', 'true_lord_consecutive_successes',
                              'consecutive_errors', 'chaos_energy', 'rift_stage', 'transfer_tasks_completed']:
                    data[field] = 0
                elif field == 'artifact_chaos_state':
                    data[field] = 'dormant'
                elif field in ['selected_tasks', 'selected_boss_tasks', 'boss_abilities_used']:
                    data[field] = []
                elif field in ['in_boss_battle', 'in_secret_level', 'just_completed_level', 
                              'true_lord_used_hint', 'true_lord_secret_unlocked', 'true_lord_epic',
                              'completed_normal_game', 'absolute_victory']:
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
                    value = [] if key not in ['achievements', 'artifact_upgrades', 'bank_data', 'castle_data', 'player_profile', 'weak_areas', 'report_preferences'] else {}
                result[key] = json.dumps(value, ensure_ascii=False) if value else None
            elif key in self.DB_COLUMNS and key not in ['game_state', 'created_at', 'user_id']:
                if key == 'first_time':
                    result[key] = 1 if value else 0
                elif key == 'parent_email' and value:
                    # 🔐 Шифруем email перед сохранением
                    result[key] = _encrypt_parent_data(value)
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
                "completed_normal_game": False, "soul_shards": 0, "absolute_victory": False,
                # 🔹 Chaos System defaults
                "consecutive_errors": 0, "chaos_energy": 0, "rift_stage": 0,
                "artifact_chaos_state": "dormant", "transfer_tasks_completed": 0,
                # 🔹 Dynamic difficulty defaults
                "difficulty_level_addition": 1, "difficulty_level_subtraction": 1,
                "difficulty_level_multiplication": 1, "difficulty_level_division": 1,
                "tasks_on_current_level": 0, "accuracy_last_10": 1.0,
                # 🔹 Monetization defaults
                "parent_email": None, "subscription_tier": "free",
                "report_preferences": None, "weak_areas": None,
                "preferred_practice_time": "any",
                # 🔹 Stats defaults
                "total_tasks_attempted": 0, "total_tasks_correct": 0,
                "accuracy_overall": 1.0, "last_session_end": None
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
        cursor.execute("DELETE FROM task_attempts WHERE user_id = ?", (user_id_int,))
        cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id_int,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id_int,))
        self.conn.commit()
        logger.info(f"🗑️ Пользователь {user_id_int} и его данные удалены")
    
    # 🔹 НОВЫЕ МЕТОДЫ для статистики и монетизации
    
    def log_task_attempt(self, user_id: int, task_id: str, island_id: str, 
                        operation_type: str, is_correct: bool, 
                        time_taken: float = None, answer_given: str = None,
                        expected_answer: str = None, chaos_energy: int = None,
                        rift_stage: int = None, transfer_used: bool = False) -> bool:
        """Логирует попытку решения задачи для статистики."""
        try:
            user_id_int = self._extract_numeric_user_id(user_id)
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO task_attempts (
                    user_id, task_id, island_id, operation_type, is_correct,
                    time_taken_seconds, answer_given, expected_answer,
                    chaos_energy, rift_stage, transfer_task_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id_int, task_id, island_id, operation_type, is_correct,
                time_taken, answer_given, expected_answer,
                chaos_energy, rift_stage, transfer_used
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка log_task_attempt: {e}")
            self.conn.rollback()
            return False
    
    def get_user_weaknesses(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Возвращает слабые зоны пользователя на основе истории."""
        user_id_int = self._extract_numeric_user_id(user_id)
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                island_id, operation_type,
                COUNT(*) as total,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                ROUND(1.0 * SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) as accuracy
            FROM task_attempts
            WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
            GROUP BY island_id, operation_type
            HAVING COUNT(*) >= 3
            ORDER BY accuracy ASC
            LIMIT ?
        """, (user_id_int, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_subscription_info(self, user_id: int) -> Dict:
        """Возвращает информацию о подписке пользователя."""
        user_id_int = self._extract_numeric_user_id(user_id)
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT subscription_status, subscription_start, subscription_end, report_frequency
            FROM subscriptions WHERE user_id = ?
        """, (user_id_int,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"subscription_status": "free"}
    
    def update_subscription(self, user_id: int, status: str, parent_email: str = None, 
                           frequency: str = 'weekly') -> bool:
        """Обновляет информацию о подписке."""
        try:
            user_id_int = self._extract_numeric_user_id(user_id)
            cursor = self.conn.cursor()
            
            # 🔐 Шифруем email если есть
            encrypted_email = _encrypt_parent_data(parent_email) if parent_email else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, parent_email, subscription_status, report_frequency, subscription_start)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (user_id_int, encrypted_email, status, frequency))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка update_subscription: {e}")
            self.conn.rollback()
            return False
    
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