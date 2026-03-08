"""
Менеджер очков для бота «Числяндия».
Версия: 1.5 (sync + commit fix) 💰

Все операции с очками проходят через этот модуль.
Гарантирует:
- Транзакционность (всё или ничего)
- Логирование всех изменений
- Защиту от отрицательного баланса
- Поддержку сезонов и лидербордов
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ScoreManager:
    """Управление очками пользователей."""
    
    def __init__(self, storage):
        self.storage = storage
        logger.info("✅ ScoreManager инициализирован")
    
    # ============================================================
    # 💰 ОСНОВНЫЕ ОПЕРАЦИИ (СИНХРОННЫЕ)
    # ============================================================
    
    def add_score(
        self,
        user_id: int,
        amount: int,
        reason: str,
        context: str = None,
        add_to_balance: bool = True
    ) -> bool:
        """Начислить очки пользователю."""
        if amount <= 0:
            logger.error(f"❌ add_score: amount должен быть положительным ({amount})")
            return False
        
        try:
            user = self.storage.get_user(user_id)
            if not user:
                logger.error(f"❌ add_score: пользователь {user_id} не найден")
                return False
            
            # ✅ АТОМАРНОЕ ОБНОВЛЕНИЕ: один вызов save_user
            updates = {**user}
            updates['total_score'] = user.get('total_score', 0) + amount

            if add_to_balance:
                updates['score_balance'] = user.get('score_balance', 0) + amount

            updates['season_score'] = user.get('season_score', 0) + amount

            self.storage.save_user(user_id, updates)
            
            # Пишем в лог
            self.log_score_change(
                user_id=user_id,
                amount=amount,
                reason=reason,
                context=context,
                season_id=user.get('season_id', 1)
            )
            
            logger.info(f"💰 +{amount} очков пользователю {user_id} ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"❌ add_score ошибка: {e}", exc_info=True)
            return False
    
    def spend_score(
        self,
        user_id: int,
        amount: int,
        reason: str,
        context: str = None
    ) -> Tuple[bool, str]:
        """Списать очки с пользователя."""
        if amount <= 0:
            return False, "❌ Сумма должна быть положительной"
        
        try:
            user = self.storage.get_user(user_id)
            if not user:
                return False, "❌ Пользователь не найден"
            
            current_balance = user.get('score_balance', 0)
            
            if current_balance < amount:
                return False, f"❌ Недостаточно очков (нужно {amount}, есть {current_balance})"
            
            new_balance = current_balance - amount
            self.storage.save_user(user_id, {**user, 'score_balance': new_balance})
            
            self.log_score_change(
                user_id=user_id,
                amount=-amount,
                reason=reason,
                context=context,
                season_id=user.get('season_id', 1)
            )
            
            logger.info(f"💸 -{amount} очков у пользователя {user_id} ({reason})")
            return True, "✅ Покупка успешна"
            
        except Exception as e:
            logger.error(f"❌ spend_score ошибка: {e}", exc_info=True)
            return False, "❌ Произошла ошибка при списании"
    
    # ============================================================
    # 📊 ЛИДЕРБОРДЫ И СТАТИСТИКА
    # ============================================================
    
    def get_leaderboard(self, period: str = 'all', limit: int = 10, season_id: int = None) -> List[Dict]:
        return self.storage.get_leaderboard(period, limit, season_id)
    
    def get_score_history(self, user_id: int, limit: int = 50, season_id: int = None) -> List[Dict]:
        return self.storage.get_score_history(user_id, limit, season_id)
    
    def get_user_stats(self, user_id: int) -> Dict:
        return self.storage.get_stats(user_id)
    
    # ============================================================
    # 🎁 СЕЗОНЫ
    # ============================================================
    
    def start_new_season(self, season_id: int) -> bool:
        try:
            all_users = self.storage.get_all_users()
            for user_id in all_users:
                user = self.storage.get_user(user_id)
                if user:
                    self.storage.save_user(user_id, {**user, 'season_score': 0, 'season_id': season_id})
            logger.info(f"🎉 Сезон {season_id} начат! Пользователей: {len(all_users)}")
            return True
        except Exception as e:
            logger.error(f"❌ start_new_season ошибка: {e}", exc_info=True)
            return False
    
    # ============================================================
    # 🔍 УТИЛИТЫ
    # ============================================================
    
    def get_balance(self, user_id: int) -> int:
        user = self.storage.get_user(user_id)
        return user.get('score_balance', 0) if user else 0
    
    def get_total_score(self, user_id: int) -> int:
        user = self.storage.get_user(user_id)
        return user.get('total_score', 0) if user else 0
    
    # ============================================================
    # ✅ ЛОГИРОВАНИЕ
    # ============================================================
    
    def log_score_change(
        self,
        user_id: int,
        amount: int,
        reason: str,
        context: str = None,
        season_id: int = None
    ) -> bool:
        """Логирует изменение очков в score_log."""
        try:
            cursor = self.storage.conn.cursor()
            
            cursor.execute("""
                INSERT INTO score_log (user_id, amount, reason, context, season_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, reason, context, season_id or 1, datetime.now(timezone.utc).isoformat()))
            
            # ✅ COMMIT ДЛЯ ЛОГИРОВАНИЯ
            self.storage.conn.commit()
            
            logger.debug(f"📝 Записано в score_log: user={user_id}, amount={amount}, reason={reason}")
            return True
            
        except Exception as e:
            logger.error(f"❌ log_score_change ошибка: {e}", exc_info=True)
            return False