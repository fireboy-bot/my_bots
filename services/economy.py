# services/economy.py
"""
Централизованная экономика — единая точка входа для всех операций.
Версия: 1.0 (Economy Entry Point) 💰✅
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class EconomyService:
    """
    Сервис экономики.
    Все операции с очками/золотом проходят через здесь.
    """
    
    def __init__(self, storage):
        self.storage = storage
    
    def add_score(self, user_id: str, amount: int, reason: str, context: str = None) -> Tuple[bool, str]:
        """
        Добавить очки пользователю.
        
        Args:
            user_id: ID пользователя
            amount: Сколько добавить (всегда положительное)
            reason: Причина (boss_task_correct, quest_reward, etc.)
            context: Дополнительный контекст (boss_id, task_id, etc.)
        
        Returns:
            (success: bool, message: str)
        """
        if amount <= 0:
            logger.error(f"❌ add_score: amount должен быть > 0, получено {amount}")
            return False, "Некорректная сумма"
        
        try:
            user_data = self.storage.get_user(user_id)
            if not user_data:
                return False, "Пользователь не найден"
            
            # Обновляем баланс
            user_data["score_balance"] = user_data.get("score_balance", 0) + amount
            user_data["total_score"] = user_data.get("total_score", 0) + amount
            
            # Сохраняем
            self.storage.save_user(user_id, user_data)
            
            # Логируем (для score_log)
            self.storage.log_score_change(
                user_id=user_id,
                amount=amount,
                reason=reason,
                context=context
            )
            
            logger.info(f"💰 +{amount} очков для user_id={user_id} (reason={reason})")
            return True, f"Добавлено {amount} очков"
            
        except Exception as e:
            logger.error(f"❌ Ошибка add_score: {e}")
            return False, f"Ошибка: {e}"
    
    def spend_score(self, user_id: str, amount: int, reason: str, context: str = None) -> Tuple[bool, str]:
        """
        Списать очки у пользователя.
        
        Args:
            user_id: ID пользователя
            amount: Сколько списать (всегда положительное)
            reason: Причина (hint_used, decoration_purchase, etc.)
            context: Дополнительный контекст
        
        Returns:
            (success: bool, message: str)
        """
        if amount <= 0:
            logger.error(f"❌ spend_score: amount должен быть > 0, получено {amount}")
            return False, "Некорректная сумма"
        
        try:
            user_data = self.storage.get_user(user_id)
            if not user_data:
                return False, "Пользователь не найден"
            
            current_balance = user_data.get("score_balance", 0)
            
            # Проверяем достаточно ли очков
            if current_balance < amount:
                return False, f"Недостаточно очков (нужно {amount}, есть {current_balance})"
            
            # Списываем
            user_data["score_balance"] = current_balance - amount
            user_data["total_score"] = user_data.get("total_score", 0) - amount
            
            # Сохраняем
            self.storage.save_user(user_id, user_data)
            
            # Логируем
            self.storage.log_score_change(
                user_id=user_id,
                amount=-amount,  # Отрицательное для списания
                reason=reason,
                context=context
            )
            
            logger.info(f"💸 -{amount} очков для user_id={user_id} (reason={reason})")
            return True, f"Списано {amount} очков"
            
        except Exception as e:
            logger.error(f"❌ Ошибка spend_score: {e}")
            return False, f"Ошибка: {e}"
    
    def get_balance(self, user_id: str) -> int:
        """Получить текущий баланс пользователя."""
        user_data = self.storage.get_user(user_id)
        if not user_
            return 0
        return user_data.get("score_balance", 0)
    
    def get_total_score(self, user_id: str) -> int:
        """Получить общий счёт пользователя."""
        user_data = self.storage.get_user(user_id)
        if not user_
            return 0
        return user_data.get("total_score", 0)


# ✅ SINGLETON для удобного доступа
_economy_instance = None

def get_economy_service(storage):
    """Получить экземпляр EconomyService."""
    global _economy_instance
    if _economy_instance is None:
        _economy_instance = EconomyService(storage)
    return _economy_instance