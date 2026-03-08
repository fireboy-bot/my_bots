# core/castle_engine.py
"""
Движок Замка — экономика декораций, upkeep, бонусы.
Версия: 1.0 (MVP) 🏰
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any, List
from database.storage import PlayerStorage

logger = logging.getLogger(__name__)

class CastleEngine:
    """Управляет экономикой Замка"""
    
    # Настройки (MVP)
    DEFAULT_UPKEEP_PER_DECORATION = 50  # золотых в день
    DECORATION_BONUS_PERCENT = 5  # % бонус к очкам за декорацию
    
    def __init__(self, storage: PlayerStorage):
        self.storage = storage
    
    def _get_castle_data(self, user: dict) -> dict:
        """Получает данные Замка из user dict"""
        castle_data = user.get("castle_data")
        
        # ✅ ИСПРАВЛЕНО: castle_data: с двоеточием
        if not castle_data:
            return {"decorations": [], "upkeep_paid_until": None}
        
        if isinstance(castle_data, str):
            try:
                return json.loads(castle_data)
            except json.JSONDecodeError:
                return {"decorations": [], "upkeep_paid_until": None}
        
        if isinstance(castle_data, dict):
            return castle_data
        
        return {"decorations": [], "upkeep_paid_until": None}
    
    def _save_castle_data(self, user_id: str, castle_data: dict):
        """Сохраняет данные Замка"""
        user = self.storage.get_user(user_id)
        if not user:
            logger.error(f"❌ Пользователь {user_id} не найден")
            return False
        
        user["castle_data"] = json.dumps(castle_data)
        self.storage.save_user(user_id, user)
        logger.info(f"✅ castle_data сохранён для user_id={user_id}")
        return True
    
    def get_castle_state(self, user_id: str) -> Dict[str, Any]:
        """Получает состояние Замка игрока"""
        user = self.storage.get_user(user_id)
        if not user:
            return {
                "decorations": [],
                "total_upkeep": 0,
                "days_left": 0,
                "bonuses_active": False,
                "bonus_percent": 0
            }
        
        castle_data = self._get_castle_data(user)
        decorations = castle_data.get("decorations", [])
        
        # Считаем upkeep
        total_upkeep = len(decorations) * self.DEFAULT_UPKEEP_PER_DECORATION
        
        # Проверяем, оплачен ли upkeep
        upkeep_paid_until = castle_data.get("upkeep_paid_until")
        
        if upkeep_paid_until:
            if isinstance(upkeep_paid_until, str):
                try:
                    paid_until = datetime.fromisoformat(upkeep_paid_until)
                    days_left = (paid_until - datetime.now(timezone.utc)).days
                    bonuses_active = days_left > 0
                except Exception:
                    days_left = 0
                    bonuses_active = False
            else:
                days_left = 0
                bonuses_active = False
        else:
            days_left = 0
            bonuses_active = False
        
        return {
            "decorations": decorations,
            "total_upkeep": total_upkeep,
            "days_left": max(0, days_left),
            "bonuses_active": bonuses_active,
            "bonus_percent": len(decorations) * self.DECORATION_BONUS_PERCENT
        }
    
    def pay_upkeep(self, user_id: str, days: int = 1) -> Tuple[bool, str]:
        """
        Оплачивает содержание Замка.
        """
        user = self.storage.get_user(user_id)
        if not user:
            return False, "❌ Игрок не найден"
        
        castle_data = self._get_castle_data(user)
        decorations = castle_data.get("decorations", [])
        total_upkeep = len(decorations) * self.DEFAULT_UPKEEP_PER_DECORATION * days
        
        if total_upkeep <= 0:
            return True, "✅ У вас нет декораций — upkeep не требуется!"
        
        current_balance = user.get("score_balance", 0)
        
        if current_balance < total_upkeep:
            return False, f"❌ Недостаточно золотых! Нужно {total_upkeep}, есть {current_balance}"
        
        user["score_balance"] = current_balance - total_upkeep
        
        new_paid_until = datetime.now(timezone.utc) + timedelta(days=days)
        castle_data["upkeep_paid_until"] = new_paid_until.isoformat()
        
        self._save_castle_data(user_id, castle_data)
        self.storage.save_user(user_id, user)
        
        logger.info(f"🏰 Upkeep оплачен: {total_upkeep} золотых за {days} день(ей)")
        
        return True, f"✅ Оплачено {total_upkeep} золотых за {days} день(ей)! Бонусы активны."
    
    def add_decoration(self, user_id: str, decoration_id: str, decoration_name: str) -> Tuple[bool, str]:
        """Добавляет декорацию в Замок"""
        user = self.storage.get_user(user_id)
        if not user:
            return False, "❌ Игрок не найден"
        
        castle_data = self._get_castle_data(user)
        decorations = castle_data.get("decorations", [])
        
        for dec in decorations:
            if dec.get("id") == decoration_id:
                return False, "⚠️ Эта декорация уже у вас есть!"
        
        decorations.append({
            "id": decoration_id,
            "name": decoration_name,
            "purchased_at": datetime.now(timezone.utc).isoformat()
        })
        
        castle_data["decorations"] = decorations
        self._save_castle_data(user_id, castle_data)
        
        logger.info(f"🏰 Декорация {decoration_name} добавлена в Замок")
        
        return True, f"✅ {decoration_name} добавлена в ваш Замок!"
    
    def get_active_bonuses(self, user_id: str) -> Dict[str, float]:
        """Возвращает активные бонусы Замка"""
        castle_state = self.get_castle_state(user_id)
        
        if not castle_state["bonuses_active"]:
            return {}
        
        return {
            "castle_decoration": 1.0 + (castle_state["bonus_percent"] / 100)
        }
    
    def calculate_upkeep_due(self, user_id: str) -> int:
        """Считает, сколько золотых нужно для оплаты upkeep"""
        castle_state = self.get_castle_state(user_id)
        return castle_state["total_upkeep"]