"""
Схема базы данных для бота «Числяндия».
Версия: 2.2 (Златочёт + bank_data поле) 🏦🗄️
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """Возвращает путь к файлу базы данных."""
    return os.path.join(os.path.dirname(__file__), "..", "data", "progress.db")


def init_database(db_path: str = None):
    """
    Создаёт и обновляет таблицы базы данных.
    """
    if db_path is None:
        db_path = get_db_path()
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ============================================
    # ТАБЛИЦА 1: users
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            
            -- 🎮 ПРОГРЕСС
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            xp_to_next INTEGER DEFAULT 50,
            
            -- 💰 СИСТЕМА ОЧКОВ
            total_score INTEGER DEFAULT 0,
            score_balance INTEGER DEFAULT 0,
            season_score INTEGER DEFAULT 0,
            season_id INTEGER DEFAULT 1,
            
            -- 📊 СТАТИСТИКА
            tasks_solved INTEGER DEFAULT 0,
            tasks_correct INTEGER DEFAULT 0,
            
            -- 🎒 КОНТЕНТ (JSON-строки)
            defeated_bosses TEXT DEFAULT '[]',
            completed_zones TEXT DEFAULT '[]',
            inventory TEXT DEFAULT '[]',
            unlocked_zones TEXT DEFAULT '["addition"]',
            rewards TEXT DEFAULT '[]',
            abilities TEXT DEFAULT '[]',
            achievements TEXT DEFAULT '{}',
            castle_decorations TEXT DEFAULT '[]',
            artifact_upgrades TEXT DEFAULT '{}',
            
            -- ✅ ЗЛАТОЧЁТ (БАНК)
            bank_data TEXT DEFAULT '{}',
            
            -- ⚙️ СОСТОЯНИЕ ИГРЫ
            game_state TEXT DEFAULT '{}',
            
            -- 📅 МЕТА-ДАННЫЕ
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============================================
    # ТАБЛИЦА 2: score_log
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS score_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,
            context TEXT,
            season_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    
    # ============================================
    # ТАБЛИЦА 3: task_history
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_type TEXT,
            difficulty TEXT,
            is_correct INTEGER,
            time_spent REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    
    # ============================================
    # ИНДЕКСЫ
    # ============================================
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_score ON users(total_score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_user ON score_log(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_time ON score_log(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON task_history(user_id)")
    
    conn.commit()
    
    # ============================================
    # 🔄 МИГРАЦИИ
    # ============================================
    _run_migrations(cursor, conn)
    
    conn.close()
    logger.info(f"✅ База данных инициализирована: {db_path}")


def _run_migrations(cursor, conn):
    """Применяет миграции к существующей базе."""
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Добавляем bank_data если нет
        if 'bank_data' not in columns:
            logger.info("🔄 Миграция: добавляем bank_data...")
            cursor.execute("ALTER TABLE users ADD COLUMN bank_data TEXT DEFAULT '{}'")
        
        conn.commit()
        logger.info("✅ Миграции применены успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        conn.rollback()
        raise