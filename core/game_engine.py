"""
Главное ядро игры Числяндия.
Версия: 3.3 (Chaos System Integration) 🧠🔮🌋✅
"""

import logging
import sqlite3
import random
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone
from database.storage import PlayerStorage, get_db_path
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
    
    # =============================================================================
    # 🔥 CHAOS SYSTEM: НОВЫЕ МЕТОДЫ
    # =============================================================================
    
    def _calculate_rift_stage(self, consecutive_errors: int) -> int:
        """
        Рассчитывает стадию Разлома на основе ошибок подряд.
        
        Стадии:
        0 = спокойно (0 ошибок)
        1 = лёгкий треск (1-2 ошибки)
        2 = числа плывут (3-4 ошибки)
        3 = нестабильность (5-6 ошибок)
        4 = перегрузка (7+ ошибок)
        """
        if consecutive_errors == 0:
            return 0
        elif consecutive_errors <= 2:
            return 1
        elif consecutive_errors <= 4:
            return 2
        elif consecutive_errors <= 6:
            return 3
        else:
            return 4
    
    def _get_artifact_chaos_state(self, chaos_energy: int, rift_stage: int) -> str:
        """
        Определяет состояние Артефакта Хаоса.
        
        Состояния:
        - 'dormant': спящий (хаос < 20)
        - 'awakened': пробуждён (хаос 20-59)
        - 'active': активный (хаос 60-99)
        - 'overload': перегрузка (хаос = 100 ИЛИ стадия 4)
        """
        if rift_stage >= 4 or chaos_energy >= 100:
            return "overload"
        elif chaos_energy >= 60:
            return "active"
        elif chaos_energy >= 20:
            return "awakened"
        else:
            return "dormant"
    
    def _generate_options(self, correct: int, min_val: int, max_val: int, count: int = 4) -> List[str]:
        """Генерирует варианты ответов (вспомогательная функция)."""
        options = {str(correct)}
        while len(options) < count:
            wrong = correct + random.randint(-15, 15)
            if wrong != correct and min_val <= wrong <= max_val:
                options.add(str(wrong))
        options_list = list(options)
        random.shuffle(options_list)
        return options_list
    
    def _generate_transfer_task(self, original_task: dict, user: dict) -> dict:
        """
        Генерирует задачу-перенос на основе оригинальной.
        🔹 ЗАЩИЩЁННАЯ ВЕРСИЯ: использует .get() с дефолтами
        """
        original_question = original_task.get("question", "Задача")
        island = original_task.get("island", "unknown")
        operation_type = original_task.get("operation_type", "unknown")
        original_options = original_task.get("options", ["8", "9", "10", "11"])  # ← ДЕФОЛТ!
        correct_answer = original_task.get("correct_answer", "8")
        base_score = original_task.get("score", 10)
    
        # 🔹 Перестановка для умножения (коммутативность)
        if island == "multiplication" and "×" in original_question:
            parts = original_question.split("×")
            if len(parts) == 2:
                a = parts[0].strip().replace("=?", "").strip()
                b = parts[1].strip().replace("=?", "").strip()
                new_question = f"{b} × {a} = ?"
            
                options = self._generate_options(int(correct_answer), min_val=int(correct_answer)-20, max_val=int(correct_answer)+20)
            
                return {
                    "id": f"transfer_{original_task.get('id', 'unknown')}",
                    "question": new_question,
                    "options": options,
                    "correct_answer": correct_answer,
                    "score": max(5, base_score - 5),
                    "island": island,
                    "operation_type": operation_type,
                    "is_transfer": True,
                    "rift_closing": True
                }
    
        # 🔹 Перестановка для сложения (коммутативность)
        if island == "addition" and "+" in original_question:
            nums = re.findall(r'\d+', original_question)
            if len(nums) >= 2:
                a, b = nums[-2], nums[-1]
                new_question = f"Сколько будет {b} + {a}?"
            else:
                parts = original_question.split("+")
                if len(parts) == 2:
                    a = parts[0].strip().replace("=?", "").strip()
                    b = parts[1].strip().replace("=?", "").strip()
                    new_question = f"{b} + {a} = ?"
                else:
                    new_question = original_question
            
            options = self._generate_options(int(correct_answer), min_val=int(correct_answer)-20, max_val=int(correct_answer)+20)
            
            return {
                "id": f"transfer_{original_task.get('id', 'unknown')}",
                "question": new_question,
                "options": options,
                "correct_answer": correct_answer,
                "score": max(5, base_score - 5),
                "island": island,
                "operation_type": operation_type,
                "is_transfer": True,
                "rift_closing": True
            }
    
        # 🔹 ЗАЩИЩЁННАЯ заглушка для других типов
        return {
            "id": f"transfer_{original_task.get('id', 'unknown')}",
            "question": original_question,
            "options": original_options,  # ← Берём из .get() с дефолтом!
            "correct_answer": correct_answer,
            "score": max(5, base_score - 5),
            "island": island,
            "operation_type": operation_type,
            "is_transfer": True,
            "rift_closing": True,
            "hint": "Примени ту же идею, но иначе!"
        }
    
    def _answers_match(self, answer: Any, expected_answer: Any) -> bool:
        """Сравнивает ответы: строка или число с допуском (как в TG)."""
        a = str(answer).strip().replace(',', '.')
        e = str(expected_answer).strip().replace(',', '.')
        if a == e:
            return True
        try:
            return abs(float(a) - float(e)) < 0.01
        except (ValueError, TypeError):
            return False

    def _get_character_message(self, user: dict, is_correct: bool, rift_stage: int) -> str:
        """Возвращает сообщение от персонажа в зависимости от ситуации."""
        # 🔹 Владимир комментирует Разлом
        if rift_stage == 0:
            if is_correct:
                return "🎩 «Превосходно, сударыня. Порядок восстановлен.»"
            else:
                return "🎩 «Числа колеблются... соберитесь, сударыня.»"
        elif rift_stage <= 2:
            return "🎩 «Смысл ускользает... попробуйте иначе.»"
        elif rift_stage == 3:
            return "🎩 «Хаос нарастает! Вспомните основу!»"
        else:  # rift_stage == 4
            return "🎩 «ПЕРЕГРУЗКА! Остановитесь. Восстановите порядок.»"
    
    # =============================================================================
    # 🔥 ОБНОВЛЁННЫЙ solve_task С CHAOS SYSTEM
    # =============================================================================
    
    def solve_task(
        self,
        user_id: str,
        answer: Any,
        task_id: str,
        expected_answer: Any,
        island_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        is_transfer: bool = False
    ) -> Dict[str, Any]:
        """
        Проверяет ответ на задачу с учётом Chaos System.
        
        Возвращает расширенный ответ для витрины:
        {
            "correct": bool,
            "reward": int,
            "message": str,
            "chaos_state": { ... },  # Для визуала Разлома/Артефакта
            "transfer_task": { ... } or None  # Если нужна задача-перенос
        }
        """
        # 🔹 Базовая проверка ответа (как в handlers/levels.py — числовое сравнение)
        is_correct = self._answers_match(answer, expected_answer)
        
        # 🔹 Получаем пользователя
        user = self.storage.get_user(user_id)
        if not user:
            return {"correct": False, "reward": 0, "message": "❌ Игрок не найден", "chaos_state": None, "transfer_task": None}

        active_level = user.get("current_level")
        if active_level and not is_transfer and user.get("selected_tasks"):
            island = island_id or active_level
            if island == active_level:
                from core.level_run import process_level_answer

                result = process_level_answer(self.storage, self.score_manager, user_id, is_correct)
                if not result.get("error"):
                    user = self.storage.get_user(user_id) or user
                    result["level_up"] = bool(result.get("player_level_up"))
                    result["chaos_state"] = {
                        "rift_stage": user.get("rift_stage", 0),
                        "chaos_energy": user.get("chaos_energy", 0),
                        "artifact_state": user.get("artifact_chaos_state", "dormant"),
                        "consecutive_errors": user.get("consecutive_errors", 0),
                    }
                    result["transfer_task"] = None
                    return result

        if user.get("in_boss_battle") and not is_transfer:
            from core.boss_run import process_boss_answer

            result = process_boss_answer(self.storage, self.score_manager, user_id, str(answer))
            if not result.get("error"):
                user = self.storage.get_user(user_id) or user
                result["level_up"] = False
                result["chaos_state"] = {
                    "rift_stage": user.get("rift_stage", 0),
                    "chaos_energy": user.get("chaos_energy", 0),
                    "artifact_state": user.get("artifact_chaos_state", "dormant"),
                    "consecutive_errors": user.get("consecutive_errors", 0),
                }
                result["transfer_task"] = None
                return result
        
        # 🔹 Обновляем статистику ошибок (Chaos System)
        if is_correct:
            user["consecutive_errors"] = 0
            user["chaos_energy"] = max(0, user.get("chaos_energy", 0) - 10)
        else:
            user["consecutive_errors"] = user.get("consecutive_errors", 0) + 1
            user["chaos_energy"] = min(100, user.get("chaos_energy", 0) + 20)
        
        # 🔹 Пересчитываем стадию Разлома и состояние Артефакта
        rift_stage = self._calculate_rift_stage(user["consecutive_errors"])
        artifact_state = self._get_artifact_chaos_state(user["chaos_energy"], rift_stage)
        
        # 🔹 Рассчитываем награду (с учётом анти-абуза)
        base_score = self._get_task_reward(task_id, user) if is_correct else 0
        base_penalty = self._get_task_penalty(task_id, user) if not is_correct else 0
        
        # 🔹 Анти-абуз: 7+ ошибок подряд = 0 наград (но штраф остаётся)
        if user["consecutive_errors"] >= 7 and is_correct:
            reward = 0
        elif is_correct:
            # 🔹 Если это задача-перенос — чуть меньше очков
            reward = base_score - 5 if is_transfer else base_score
            reward = max(5, reward)  # Минимум 5 очков
        else:
            reward = base_penalty
        
        # 🔹 Применяем награду/штраф через ScoreManager (если не перегрузка)
        if reward != 0:
            if reward > 0:
                self.score_manager.add_score(
                    user_id=user_id,
                    amount=reward,
                    reason="task_correct" if not is_transfer else "transfer_correct",
                    context=task_id,
                    apply_artifacts=True
                )
            else:
                self.score_manager.apply_penalty(
                    user_id=user_id,
                    base_penalty=abs(reward),
                    reason="task_mistake",
                    context=task_id
                )
            # score_manager пишет в БД — подтягиваем актуальный баланс, иначе save_user ниже откатит
            refreshed = self.storage.get_user(user_id)
            if refreshed:
                user["score_balance"] = refreshed.get("score_balance", user.get("score_balance", 0))
                user["total_score"] = refreshed.get("total_score", user.get("total_score", 0))
        
        # 🔹 Генерируем задачу-перенос если нужна (ошибка + 2+ подряд + НЕ уже перенос)
        transfer_task = None
        if not is_correct and not is_transfer and user["consecutive_errors"] >= 2:
            from core.task_loader import get_task_by_id

            original_task = get_task_by_id(task_id, island_id)
            if not original_task:
                original_task = {
                    "id": task_id,
                    "question": f"Задача {task_id}",
                    "correct_answer": str(expected_answer),
                    "score": base_score,
                    "island": island_id or "unknown",
                    "operation_type": operation_type or "unknown",
                }
            transfer_task = self._generate_transfer_task(original_task, user)
        
        # 🔹 Сообщение от персонажа
        message = self._get_character_message(user, is_correct, rift_stage)
        
        # 🔹 Обновляем общую статистику
        user["total_tasks_attempted"] = user.get("total_tasks_attempted", 0) + 1
        if is_correct:
            user["total_tasks_correct"] = user.get("total_tasks_correct", 0) + 1
            if user["total_tasks_attempted"] > 0:
                user["accuracy_overall"] = round(
                    user["total_tasks_correct"] / user["total_tasks_attempted"] * 100, 1
                )
        
        # 🔹 Обновляем уровень если нужно
        level_up = self._check_level_progress(user_id, user)
        
        # 🔹 Сохраняем пользователя с новыми полями Хаоса
        user["rift_stage"] = rift_stage
        user["artifact_chaos_state"] = artifact_state
        if is_transfer and is_correct:
            user["transfer_tasks_completed"] = user.get("transfer_tasks_completed", 0) + 1
        
        self.storage.save_user(user_id, user)
        
        # 🔹 Логируем попытку для статистики (если есть метод)
        try:
            self.storage.log_task_attempt(
                user_id=user_id,
                task_id=task_id,
                island_id=island_id or "unknown",
                operation_type=operation_type or "unknown",
                is_correct=is_correct,
                time_taken=None,
                answer_given=str(answer),
                expected_answer=str(expected_answer),
                chaos_energy=user["chaos_energy"],
                rift_stage=rift_stage,
                transfer_used=is_transfer
            )
        except AttributeError:
            # Метод может ещё не существовать в старой версии storage.py
            pass
        
        # 🔹 Возвращаем расширенный ответ для витрины
        return {
            "correct": is_correct,
            "reward": reward,
            "message": message,
            "level_up": level_up,
            "chaos_state": {
                "rift_stage": rift_stage,
                "chaos_energy": user["chaos_energy"],
                "artifact_state": artifact_state,
                "consecutive_errors": user["consecutive_errors"]
            },
            "transfer_task": transfer_task,
            "new_balance": user.get("score_balance", 0),
            "new_total_score": user.get("total_score", 0)
        }
    
    # =============================================================================
    # 🔥 СТАРЫЕ МЕТОДЫ (СОХРАНЕНЫ)
    # =============================================================================
    
    def _get_task_reward(self, task_id: str, user: Dict) -> int:
        """Базовая награда за задачу"""
        return 50
    
    def _get_task_penalty(self, task_id: str, user: Dict) -> int:
        """Базовый штраф за ошибку"""
        return -25
    
    def _check_level_progress(self, user_id: str, user: Dict) -> bool:
        """Проверяет, завершён ли уровень"""
        # 🔹 Заглушка — в реальности проверять прогресс острова
        return False

    def _bank_conn(self) -> sqlite3.Connection:
        """Соединение с той же БД, что и storage (не хардкод пути)."""
        return sqlite3.connect(get_db_path())

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
        conn = self._bank_conn()
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
        conn = self._bank_conn()
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
        conn = self._bank_conn()
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

    def start_level_run(self, user_id: str, world_id: str) -> Dict[str, Any]:
        """Старт структурированного забега по острову (как enter_level в TG)."""
        from core.level_run import start_level_run

        return start_level_run(self.storage, user_id, world_id)

    def start_boss_run(self, user_id: str, boss_id: Optional[str] = None) -> Dict[str, Any]:
        from core.boss_run import start_boss_run

        return start_boss_run(self.storage, user_id, boss_id)

    def get_boss_state(self, user_id: str) -> Dict[str, Any]:
        from core.boss_run import get_boss_state

        user = self.storage.get_user(user_id)
        if not user:
            return {"error": "Игрок не найден"}
        state = get_boss_state(user)
        if not state:
            return {"active": False}
        return {"active": True, **state}

    def exit_boss_run(self, user_id: str) -> Dict[str, Any]:
        from core.boss_run import exit_boss_run

        return exit_boss_run(self.storage, user_id)

    def get_random_task(self, user_id: str, world: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Выдать случайную задачу — единый источник data/worlds/ (как TG)."""
        from core.task_loader import pick_task_for_user
        return pick_task_for_user(self.storage, user_id, world)

    def get_worlds(self, user_id: str) -> Dict[str, Any]:
        """Каталог миров с учётом unlocked_zones игрока."""
        from core.progression import list_worlds_for_user

        user = self.storage.get_user(user_id)
        if not user:
            return {"error": "Игрок не найден"}
        return {
            "user_id": user_id,
            "unlocked_zones": user.get("unlocked_zones", ["addition"]),
            "worlds": list_worlds_for_user(user),
        }

    def resolve_task_answer(
        self,
        task_id: str,
        island_id: Optional[str] = None,
        client_expected: Any = None,
    ) -> Optional[str]:
        """Правильный ответ по task_id — ядро, не web."""
        from core.task_loader import resolve_expected_answer
        return resolve_expected_answer(task_id, island_id, client_expected)
    
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
            "artifact_upgrades": user.get("artifact_upgrades", {}),
            "defeated_bosses": user.get("defeated_bosses", []),
            "unlocked_zones": user.get("unlocked_zones", ["addition"]),
            "completed_normal_game": user.get("completed_normal_game", False),
            # 🔹 Chaos System поля для витрины
            "chaos_energy": user.get("chaos_energy", 0),
            "rift_stage": user.get("rift_stage", 0),
            "artifact_chaos_state": user.get("artifact_chaos_state", "dormant"),
            "consecutive_errors": user.get("consecutive_errors", 0)
        }
    
    def get_artifact_info(self, user_id: str) -> Dict[str, Any]:
        """Получает информацию об артефактах игрока"""
        return self.score_manager.artifact_manager.get_all_artifacts(user_id)
    
    def upgrade_artifact(self, user_id: str, artifact_id: str) -> Tuple[bool, str]:
        """Улучшить артефакт"""
        return self.score_manager.artifact_manager.upgrade_artifact(user_id, artifact_id)

    def craft_alchemy(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Создать алхимический предмет — та же логика, что в Telegram."""
        from handlers.alchemy import craft_alchemy_item, get_alchemy_activation_message

        success, message = craft_alchemy_item(user_id, item_id, self.storage, self.score_manager)
        return {
            "success": success,
            "message": message,
            "activation": get_alchemy_activation_message(item_id) if success else None,
        }