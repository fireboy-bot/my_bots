# core/score_manager.py
"""
Управление очками и балансом игрока.
Версия: 2.1 (Artifact Manager Init Fix) 💰🔮✅
"""

import logging
from typing import Dict, Tuple, Optional
from database.storage import PlayerStorage
from core.artifact_manager import ArtifactManager

logger = logging.getLogger(__name__)


class ScoreManager:
    """Управление очками, балансом и артефактами"""
    
    def __init__(self, storage: PlayerStorage, castle_engine=None):
        self.storage = storage
        self.castle_engine = castle_engine
        # ✅ ИНИЦИАЛИЗИРУЕМ ArtifactManager
        self.artifact_manager = ArtifactManager(storage, castle_engine)
        logger.info("✅ ScoreManager инициализирован с ArtifactManager")
    
    def get_balance(self, user_id: str) -> int:
        """Получает текущий баланс игрока"""
        user = self.storage.get_user(user_id)
        if not user:
            return 0
        return user.get("score_balance", 0)
    
    def get_total_score(self, user_id: str) -> int:
        """Получает общий счёт (рейтинг) игрока"""
        user = self.storage.get_user(user_id)
        if not user:
            return 0
        return user.get("total_score", 0)
    
    def add_score(
        self,
        user_id: str,
        amount: int,
        reason: str,
        context: str = None,
        apply_artifacts: bool = True
    ) -> int:
        """
        Начисляет очки игроку.
        
        Args:
            user_id: ID пользователя
            amount: Количество очков (базовое, без бонусов)
            reason: Причина начисления (для логов)
            context: Дополнительный контекст (уровень, босс, и т.д.)
            apply_artifacts: Применить бонусы артефактов (по умолчанию True)
        
        Returns:
            int: Фактически начисленная сумма (с бонусами)
        """
        user = self.storage.get_user(user_id)
        if not user:
            logger.warning(f"⚠️ Игрок {user_id} не найден для начисления очков")
            return 0
        
        # ✅ Применяем бонус Артефакта Удачи (если включено)
        final_amount = amount
        if apply_artifacts and amount > 0:
            final_amount = self.artifact_manager.apply_score_bonus(user_id, amount)
        
        # Обновляем баланс
        old_balance = user.get("score_balance", 0)
        old_total = user.get("total_score", 0)
        
        user["score_balance"] = old_balance + final_amount
        user["total_score"] = old_total + final_amount
        
        self.storage.save_user(user_id, user)
        
        # Логируем
        logger.info(
            f"💰 SCORE: user_id={user_id}, +{final_amount} ({reason}), "
            f"balance: {old_balance} → {user['score_balance']}, "
            f"total: {old_total} → {user['total_score']}"
        )
        
        # Логируем в score_log
        self.log_score_change(user_id, final_amount, reason, context)
        
        return final_amount
    
    def spend_score(
        self,
        user_id: str,
        amount: int,
        reason: str,
        context: str = None
    ) -> Tuple[bool, str]:
        """
        Списывает очки игрока.
        
        Returns:
            (success: bool, message: str)
        """
        user = self.storage.get_user(user_id)
        if not user:
            return False, "❌ Игрок не найден"
        
        balance = user.get("score_balance", 0)
        if balance < amount:
            return False, f"❌ Недостаточно очков! Нужно {amount}, есть {balance}"
        
        user["score_balance"] = balance - amount
        self.storage.save_user(user_id, user)
        
        logger.info(
            f"💸 SPEND: user_id={user_id}, -{amount} ({reason}), "
            f"balance: {balance} → {user['score_balance']}"
        )
        
        self.log_score_change(user_id, -amount, reason, context)
        
        return True, f"✅ Списано {amount} очков"
    
    def apply_penalty(
        self,
        user_id: str,
        base_penalty: int,
        reason: str = "mistake",
        context: str = None
    ) -> int:
        """
        Применяет штраф за ошибку (с учётом Артефакта Силы).
        
        Args:
            user_id: ID пользователя
            base_penalty: Базовый штраф (отрицательное число, например -25)
            reason: Причина штрафа
            context: Дополнительный контекст
        
        Returns:
            int: Фактический штраф (с учётом артефактов)
        """
        # ✅ Применяем снижение от Артефакта Силы
        final_penalty = self.artifact_manager.apply_penalty_reduction(user_id, base_penalty)
        
        user = self.storage.get_user(user_id)
        if not user:
            return final_penalty
        
        old_balance = user.get("score_balance", 0)
        old_total = user.get("total_score", 0)
        
        user["score_balance"] = old_balance + final_penalty  # final_penalty отрицательный
        user["total_score"] = max(0, old_total + final_penalty)  # total_score не уходит в минус
        
        self.storage.save_user(user_id, user)
        
        logger.info(
            f"⚠️ PENALTY: user_id={user_id}, {base_penalty} → {final_penalty} ({reason}), "
            f"balance: {old_balance} → {user['score_balance']}"
        )
        
        self.log_score_change(user_id, final_penalty, reason, context)
        
        return final_penalty
    
    def log_score_change(
        self,
        user_id: str,
        amount: int,
        reason: str,
        context: str = None
    ) -> bool:
        """Логирует изменение очков в score_log"""
        try:
            user = self.storage.get_user(user_id)
            season_id = user.get("season_id", 1) if user else 1
            
            self.storage.log_score_change(
                user_id=user_id,
                amount=amount,
                reason=reason,
                context=context,
                season_id=season_id
            )
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка log_score_change: {e}")
            return False
    
    def transfer_score(
        self,
        from_user_id: str,
        to_user_id: str,
        amount: int,
        reason: str = "transfer"
    ) -> Tuple[bool, str]:
        """Переводит очки между игроками"""
        success, message = self.spend_score(from_user_id, amount, reason)
        if not success:
            return False, message
        
        self.add_score(to_user_id, amount, reason)
        
        logger.info(f"🔄 TRANSFER: {from_user_id} → {to_user_id}, {amount} очков")
        
        return True, f"✅ Переведено {amount} очков"
    
    def reset_score(self, user_id: str) -> bool:
        """Сбрасывает баланс и рейтинг игрока (админ)"""
        user = self.storage.get_user(user_id)
        if not user:
            return False
        
        user["score_balance"] = 0
        user["total_score"] = 0
        self.storage.save_user(user_id, user)
        
        logger.info(f"🗑️ RESET: user_id={user_id}, score сброшен")
        
        return True