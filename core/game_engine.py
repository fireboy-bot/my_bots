# core/game_engine.py
"""
Ядро Числяндии — бизнес-логика, независимая от платформы.
Telegram, Web, VK — все используют этот интерфейс.
Версия: 1.0 (MVP)
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from database.storage import PlayerStorage
from core.score_manager import ScoreManager
from core.difficulty_manager import DifficultyManager
from core.castle_engine import CastleEngine
from core.bank_manager import BankManager

class ChislyandiaEngine:
    """
    Главный класс игры.
    Все платформы (Telegram, Web, etc.) обращаются к этому интерфейсу.
    """
    
    def __init__(self, storage: PlayerStorage, score_manager: ScoreManager):
        self.storage = storage
        self.score_manager = score_manager
        self.difficulty = DifficultyManager(storage)
        self.castle = CastleEngine(storage)
        self.bank = BankManager(storage, score_manager)
    
    # ================================
    # 🧮 ЗАДАЧИ
    # ================================
    
    def solve_task(self, user_id: str, answer: int, task_id: str, expected_answer: int) -> Dict[str, Any]:
        """
        Универсальная логика решения задачи.
        
        Args:
            user_id: ID игрока
            answer: Ответ игрока
            task_id: ID задачи (например, "addition_level_3_task_12")
            expected_answer: Правильный ответ
            
        Returns:
            {
                'correct': bool,
                'score_earned': int,
                'level_up': bool,
                'message': str
            }
        """
        user = self.storage.get_user(user_id)
        is_correct = (answer == expected_answer)
        
        # Начисление очков
        if is_correct:
            base_score = 25
            multiplier = self.difficulty.get_score_multiplier(user_id, task_id)
            earned = int(base_score * multiplier)
            self.score_manager.add_score(user_id, earned, reason="task_correct", context=task_id)
        else:
            earned = 0
        
        # Адаптация сложности
        consecutive = user.get("consecutive_correct", 0) if user else 0
        island_id = task_id.split("_")[0] if "_" in task_id else "addition"
        new_level, change = self.difficulty.adjust_level(
            user_id, 
            island_id,
            is_correct,
            consecutive + 1 if is_correct else 0
        )
        
        return {
            "correct": is_correct,
            "score_earned": earned,
            "level_up": change == "level_up",
            "message": self._get_response_message(is_correct, change),
        }
    
    def _get_response_message(self, is_correct: bool, change: str) -> str:
        """Генерация сообщения (платформа сама решит, как показать)"""
        if is_correct:
            if change == "level_up":
                return "✨ Отлично! Задачки становятся сложнее, но ты справляешься!"
            return "✅ Правильно! Так держать!"
        else:
            if change == "level_down":
                return "💪 Ничего! Давай чуть проще — и ты снова в строю!"
            return "❌ Почти! Попробуй ещё раз."
    
    # ================================
    # 🏦 ЗЛАТОЧЁТ (БАНК)
    # ================================
    
    def get_bank_info(self, user_id: str) -> Dict[str, Any]:
        """Получить информацию о вкладе"""
        return self.bank.get_bank_data(user_id)
    
    def deposit_to_bank(self, user_id: str, amount: int) -> Dict[str, Any]:
        """Положить золотые в Златочёт"""
        success, message = self.bank.deposit(user_id, amount)
        return {
            "success": success,
            "message": message
        }
    
    def withdraw_from_bank(self, user_id: str) -> Dict[str, Any]:
        """Забрать вклад с процентами"""
        success, message, total = self.bank.withdraw(user_id)
        return {
            "success": success,
            "message": message,
            "total": total
        }
    
    # ================================
    # 🏰 ЗАМОК
    # ================================
    
    def get_castle_info(self, user_id: str) -> Dict[str, Any]:
        """Получить информацию о Замке"""
        return self.castle.get_castle_state(user_id)
    
    def pay_castle_upkeep(self, user_id: str) -> Dict[str, Any]:
        """Оплатить содержание Замка"""
        success, message = self.castle.pay_upkeep(user_id)
        return {
            "success": success,
            "message": message
        }
    
    # ================================
    # 🛍️ МАГАЗИН (заглушка)
    # ================================
    
    def buy_item(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Покупка предмета (будет реализовано полностью позже)"""
        # Пока заглушка — реальная логика в handlers/shop.py
        return {
            "success": False,
            "message": "🚧 Покупки через ядро — в разработке. Используйте магазин в боте."
        }
    
    # ================================
    # 👤 ПРОФИЛЬ
    # ================================
    
    def get_player_profile(self, user_id: str) -> Dict[str, Any]:
        """Получить профиль игрока (универсальный формат)"""
        user = self.storage.get_user(user_id)
        if not user:
            return {"error": "Player not found"}
        
        return {
            "user_id": user_id,
            "level": user.get("level", 1),
            "xp": user.get("xp", 0),
            "score_balance": user.get("score_balance", 0),
            "total_score": user.get("total_score", 0),
            "tasks_solved": user.get("tasks_solved", 0),
            "tasks_correct": user.get("tasks_correct", 0),
        }