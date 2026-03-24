# core/game_engine.py
"""
Главное ядро игры Числяндия.
Версия: 3.2 (Fix: Bank Info Direct DB Read) 🧠🔮🏦✅
"""

import logging
import sqlite3
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from database.storage import PlayerStorage
from core.score_manager import ScoreManager
from core.castle_engine import CastleEngine

logger = logging.getLogger(__name__)


class ChislyandiaEngine:
    """Главный класс игры — единая точка входа для всех платформ"""
    
    def __init__(self, storage: PlayerStorage, score_manager: ScoreManager):
        self.storage = storage
        self.score_manager = score_manager
        self.castle = CastleEngine(storage)
        
        logger.info("✅ ChislyandiaEngine (ядро) инициализировано")
    
    def solve_task(
        self,
        user_id: str,
        answer: Any,
        task_id: str,
        expected_answer: Any
    ) -> Dict[str, Any]:
        """Проверяет ответ на задачу"""
        user = self.storage.get_user(user_id)
        if not user:
            return {"correct": False, "message": "❌ Игрок не найден"}
        
        is_correct = (answer == expected_answer)
        
        if is_correct:
            base_score = self._get_task_reward(task_id, user)
            final_score = self.score_manager.add_score(
                user_id=user_id,
                amount=base_score,
                reason="task_correct",
                context=task_id,
                apply_artifacts=True
            )
            level_up = self._check_level_progress(user_id, user)
            
            return {
                "correct": True,
                "score_earned": final_score,
                "level_up": level_up,
                "message": f"✅ Правильно! +{final_score} очков"
            }
        else:
            base_penalty = self._get_task_penalty(task_id, user)
            final_penalty = self.score_manager.apply_penalty(
                user_id=user_id,
                base_penalty=base_penalty,
                reason="task_mistake",
                context=task_id
            )
            
            return {
                "correct": False,
                "score_earned": final_penalty,
                "level_up": False,
                "message": f"❌ Ошибка! {final_penalty} очков"
            }
    
    def _get_task_reward(self, task_id: str, user: Dict) -> int:
        """Базовая награда за задачу"""
        return 50
    
    def _get_task_penalty(self, task_id: str, user: Dict) -> int:
        """Базовый штраф за ошибку"""
        return -25
    
    def _check_level_progress(self, user_id: str, user: Dict) -> bool:
        """Проверяет, завершён ли уровень"""
        return False

    def _ensure_bank_columns(self, conn: sqlite3.Connection):
        """Гарантирует наличие банковских колонок в users."""
        c = conn.cursor()
        c.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in c.fetchall()}

        migrations = [
            ("bank_balance", "INTEGER DEFAULT 0"),
            ("interest_earned", "INTEGER DEFAULT 0"),
            ("bank_interest", "REAL DEFAULT 0.10"),
            ("bank_days", "INTEGER DEFAULT 0"),
            ("bank_last_interest_at", "TEXT"),
        ]
        for name, ddl in migrations:
            if name not in cols:
                c.execute(f"ALTER TABLE users ADD COLUMN {name} {ddl}")
        conn.commit()

    def _apply_bank_interest(self, conn: sqlite3.Connection, user_id: str):
        """
        Начисляет проценты за полные прошедшие дни с момента последнего начисления.
        Вызывается при просмотре банка/вкладе/снятии.
        """
        c = conn.cursor()
        c.execute(
            """
            SELECT bank_balance, interest_earned, bank_interest, bank_days, bank_last_interest_at
            FROM users WHERE user_id = ?
            """,
            (str(user_id),)
        )
        row = c.fetchone()
        if not row:
            return

        bank_balance = row[0] or 0
        interest_earned = row[1] or 0
        bank_interest = row[2] if row[2] is not None else 0.10
        bank_days = row[3] or 0
        last_interest_at = row[4]

        if bank_balance <= 0:
            # Если вклада нет — просто фиксируем точку отсчёта.
            if not last_interest_at:
                c.execute(
                    "UPDATE users SET bank_last_interest_at = ? WHERE user_id = ?",
                    (datetime.now(timezone.utc).isoformat(), str(user_id))
                )
                conn.commit()
            return

        now = datetime.now(timezone.utc)
        if not last_interest_at:
            c.execute(
                "UPDATE users SET bank_last_interest_at = ? WHERE user_id = ?",
                (now.isoformat(), str(user_id))
            )
            conn.commit()
            return

        try:
            last_dt = datetime.fromisoformat(last_interest_at)
        except Exception:
            last_dt = now

        full_days = int((now - last_dt).total_seconds() // 86400)
        if full_days <= 0:
            return

        add_interest = int(bank_balance * bank_interest * full_days)
        new_interest = interest_earned + add_interest
        new_days = bank_days + full_days

        c.execute(
            """
            UPDATE users
            SET interest_earned = ?, bank_days = ?, bank_last_interest_at = ?
            WHERE user_id = ?
            """,
            (new_interest, new_days, now.isoformat(), str(user_id))
        )
        conn.commit()
    
    def get_bank_info(self, user_id: str) -> Dict[str, Any]:
        """
        Получает информацию о банке.
        ✅ ЧИТАЕТ БАНКОВСКИЕ ПОЛЯ НАПРЯМУЮ ИЗ БАЗЫ (минуя кэш!)
        """
        # ✅ Прямое чтение банковских полей из базы
        conn = sqlite3.connect("data/progress.db")
        c = conn.cursor()
        self._ensure_bank_columns(conn)
        self._apply_bank_interest(conn, user_id)
        c.execute(
            "SELECT bank_balance, interest_earned, bank_interest, bank_days FROM users WHERE user_id = ?",
            (str(user_id),)
        )
        row = c.fetchone()
        conn.close()
        
        bank_balance = row[0] if row and row[0] else 0
        interest_earned = row[1] if row and row[1] else 0
        bank_interest = row[2] if row and row[2] else 0.10
        bank_days = row[3] if row and row[3] else 0
        
        # Остальные поля из кэша (это ОК)
        user = self.storage.get_user(user_id)
        if not user:
            return {"error": "Игрок не найден"}
        
        return {
            "balance": user.get("score_balance", 0),  # На руках (из кэша)
            "bank_balance": bank_balance,  # В банке (из базы!) ✅
            "interest_earned": interest_earned,  # Проценты (из базы!) ✅
            "bank_interest": bank_interest,  # Ставка (из базы!) ✅
            "days_passed": bank_days,  # Дней (из базы!) ✅
        }
    
    def deposit_to_bank(self, user_id: str, amount: int) -> Tuple[bool, str]:
        """
        Положить золото в банк.
        ✅ ПРЯМОЕ ОБНОВЛЕНИЕ БАЗЫ — минуя save_user()!
        """
        user = self.storage.get_user(user_id)
        if not user:
            return (False, "❌ Игрок не найден")
        
        current_balance = user.get("score_balance", 0)
        if current_balance < amount:
            return (False, f"❌ Недостаточно золота! Нужно {amount:,}, есть {current_balance:,}")
        
        # Списываем с баланса через ScoreManager
        success, message = self.score_manager.spend_score(
            user_id=user_id,
            amount=amount,
            reason="bank_deposit"
        )
        
        if not success:
            return (False, message)
        
        # ✅ ПРЯМО ОБНОВЛЯЕМ bank_balance В БАЗЕ!
        conn = sqlite3.connect("data/progress.db")
        c = conn.cursor()
        self._ensure_bank_columns(conn)
        self._apply_bank_interest(conn, user_id)
        
        c.execute("SELECT bank_balance FROM users WHERE user_id = ?", (str(user_id),))
        row = c.fetchone()
        current_bank = row[0] if row and row[0] else 0
        
        new_bank = current_bank + amount
        c.execute(
            """
            UPDATE users
            SET bank_balance = ?, bank_last_interest_at = ?
            WHERE user_id = ?
            """,
            (new_bank, datetime.now(timezone.utc).isoformat(), str(user_id))
        )
        conn.commit()
        conn.close()
        
        logger.info(f"🏦 Вклад: user_id={user_id}, +{amount} в банк ({current_bank} → {new_bank})")
        
        return (True, f"✅ Вклад успешен! Положено {amount:,} золотых в Златочёт.")
    
    def withdraw_from_bank(self, user_id: str) -> Tuple[bool, str, int]:
        """
        Забрать вклад с процентами.
        ✅ ПРЯМОЕ ОБНОВЛЕНИЕ БАЗЫ + кортеж (bool, str, int)
        """
        conn = sqlite3.connect("data/progress.db")
        c = conn.cursor()
        self._ensure_bank_columns(conn)
        self._apply_bank_interest(conn, user_id)
        c.execute("SELECT bank_balance, interest_earned FROM users WHERE user_id = ?", (str(user_id),))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return (False, "❌ Игрок не найден", 0)
        
        bank_balance = row[0] if row[0] else 0
        interest_earned = row[1] if row[1] else 0
        
        if bank_balance <= 0:
            conn.close()
            return (False, "❌ Вклад пуст. Нечего забирать!", 0)
        
        total = bank_balance + interest_earned
        
        # ✅ ПРЯМО ОБНОВЛЯЕМ БАЗУ: обнуляем вклад
        c.execute(
            """
            UPDATE users
            SET bank_balance = 0, interest_earned = 0, bank_days = 0, bank_last_interest_at = ?
            WHERE user_id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), str(user_id))
        )
        conn.commit()
        conn.close()
        
        # Начисляем очки на баланс через ScoreManager
        self.score_manager.add_score(user_id, total, reason="bank_withdraw")
        
        logger.info(f"🏦 Снятие: user_id={user_id}, забрано {total:,} (вклад: {bank_balance}, проценты: {interest_earned})")
        
        message = f"✅ Забрано {total:,} очков!\n💰 Вклад: {bank_balance:,}\n📈 Проценты: {interest_earned:,}"
        
        return (True, message, total)
    
    def get_castle_info(self, user_id: str) -> Dict[str, Any]:
        """Получает информацию о замке"""
        return self.castle.get_castle_state(user_id)
    
    def pay_castle_upkeep(self, user_id: str, days: int = 1) -> Tuple[bool, str]:
        """Оплатить содержание замка"""
        return self.castle.pay_upkeep(user_id, days)
    
    def get_player_profile(self, user_id: str) -> Dict[str, Any]:
        """Получает профиль игрока"""
        user = self.storage.get_user(user_id)
        if not user:
            return {"error": "Игрок не найден"}
        
        return {
            "user_id": user_id,
            "level": user.get("level", 1),
            "xp": user.get("xp", 0),
            "total_score": user.get("total_score", 0),
            "score_balance": user.get("score_balance", 0),
            "tasks_solved": user.get("tasks_solved", 0),
            "tasks_correct": user.get("tasks_correct", 0),
            "inventory": user.get("inventory", []),
            "artifact_upgrades": user.get("artifact_upgrades", {})
        }
    
    def get_artifact_info(self, user_id: str) -> Dict[str, Any]:
        """Получает информацию об артефактах игрока"""
        return self.score_manager.artifact_manager.get_all_artifacts(user_id)
    
    def upgrade_artifact(self, user_id: str, artifact_id: str) -> Tuple[bool, str]:
        """Улучшить артефакт"""
        return self.score_manager.artifact_manager.upgrade_artifact(user_id, artifact_id)