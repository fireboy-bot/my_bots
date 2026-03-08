# core/bank_manager.py
"""
Златочёт — Банк Числяндии.
Версия: 1.10 (Fix: debug logging) 🏦🔍
"""

import logging
import json
from datetime import datetime, timezone
from typing import Tuple, Dict, Any
from database.storage import PlayerStorage
from core.score_manager import ScoreManager

logger = logging.getLogger(__name__)

class BankManager:
    def __init__(self, storage: PlayerStorage, score_manager: ScoreManager):
        self.storage = storage
        self.score_manager = score_manager
    
    def _get_bank_data(self, user: dict) -> dict:
        """Получает данные банка из user dict"""
        if not user:
            return {}
        
        bank_data = user.get("bank_data")
        
        # 🔍 ЛОГ: что получили из user
        logger.debug(f"🔍 _get_bank_data: raw bank_data = {bank_data} (type: {type(bank_data)})")
        
        if bank_data is None:
            return {}
        
        if isinstance(bank_data, str):
            try:
                result = json.loads(bank_data)
                logger.debug(f"🔍 _get_bank_data: распарсили JSON → {result}")
                return result
            except Exception as e:
                logger.error(f"❌ _get_bank_data: ошибка парсинга JSON: {e}")
                return {}
        
        if isinstance(bank_data, dict):
            logger.debug(f"🔍 _get_bank_data: уже dict → {bank_data}")
            return bank_data
        
        logger.warning(f"⚠️ _get_bank_data: неизвестный тип: {type(bank_data)}")
        return {}
    
    def get_bank_data(self, user_id: int) -> Dict[str, Any]:
        """Получить данные банка игрока"""
        user = self.storage.get_user(user_id)
        logger.debug(f"🔍 get_bank_data: user = {user is not None}")
        
        if not user:
            return {"balance": 0, "deposited_at": None, "interest_earned": 0, "days_passed": 0}
        
        bank_data = self._get_bank_data(user)
        
        balance = bank_data.get("balance", 0)
        deposited_at = bank_data.get("deposited_at")
        
        # Рассчитываем проценты
        if deposited_at and isinstance(deposited_at, str):
            try:
                deposited_at = datetime.fromisoformat(deposited_at)
            except Exception:
                deposited_at = None
        
        if deposited_at and isinstance(deposited_at, datetime):
            days_passed = (datetime.now(timezone.utc) - deposited_at).days
            interest_earned = int(balance * 0.10 * days_passed)
        else:
            days_passed = 0
            interest_earned = 0
        
        return {
            "balance": balance,
            "deposited_at": deposited_at.isoformat() if deposited_at else None,
            "interest_earned": interest_earned,
            "days_passed": days_passed
        }
    
    def deposit(self, user_id: int, amount: int) -> Tuple[bool, str]:
        """Положить золотые в Златочёт"""
        logger.info(f"🏦 ДЕПОЗИТ СТАРТ: user_id={user_id}, amount={amount}")
        
        if amount < 100:
            return False, "❌ Минимальный вклад: 100 золотых"
        
        # ✅ Получаем пользователя
        user = self.storage.get_user(user_id)
        if not user:
            logger.error(f"❌ Игрок не найден: user_id={user_id}")
            return False, "❌ Игрок не найден"
        
        logger.debug(f"🔍 deposit: user keys = {list(user.keys())}")
        logger.debug(f"🔍 deposit: user['bank_data'] = {user.get('bank_data')}")
        
        current_balance = user.get("score_balance", 0)
        logger.info(f"📊 Баланс ДО: {current_balance}")
        
        if current_balance < amount:
            return False, f"❌ Недостаточно золотых на балансе! Есть: {current_balance}"
        
        # ✅ Получаем bank_data
        bank_data = self._get_bank_data(user)
        old_balance = bank_data.get("balance", 0)
        new_balance = old_balance + amount
        
        bank_data["balance"] = new_balance
        bank_data["deposited_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"🏦 Вклад: {old_balance} → {new_balance}")
        logger.debug(f"🔍 deposit: bank_data перед сохранением = {bank_data}")
        
        # ✅ Обновляем пользователя
        user["score_balance"] = current_balance - amount
        user["bank_data"] = bank_data
        
        logger.debug(f"🔍 deposit: user['bank_data'] перед save = {user['bank_data']}")
        
        # ✅ Сохраняем через PlayerStorage
        result = self.storage.save_user(user_id, user)
        logger.info(f"💾 SAVE_USER результат: {result}")
        
        # ✅ ПРОВЕРКА: читаем сразу после сохранения
        test_user = self.storage.get_user(user_id)
        logger.debug(f"🔍 ПРОВЕРКА: test_user = {test_user is not None}")
        if test_user:
            logger.debug(f"🔍 ПРОВЕРКА: test_user['bank_data'] = {test_user.get('bank_data')}")
            test_bank = self._get_bank_data(test_user)
            logger.info(f"🔍 ПРОВЕРКА: после сохранения баланс в банке = {test_bank.get('balance')}")
        else:
            logger.error("❌ ПРОВЕРКА: test_user = None!")
        
        return True, f"✅ Положено {amount} золотых в Златочёт! (10% в день)"
    
    def withdraw(self, user_id: int) -> Tuple[bool, str, int]:
        """Забрать вклад с процентами"""
        logger.info(f"🏦 СНЯТИЕ СТАРТ: user_id={user_id}")
        
        user = self.storage.get_user(user_id)
        if not user:
            return False, "❌ Игрок не найден", 0
        
        bank_data = self._get_bank_data(user)
        base_balance = bank_data.get("balance", 0)
        logger.info(f"📊 Вклад в банке: {base_balance}")
        
        if base_balance <= 0:
            return False, "❌ У вас нет вклада в Златочёте", 0
        
        # Рассчитываем проценты
        deposited_at = bank_data.get("deposited_at")
        if deposited_at and isinstance(deposited_at, str):
            try:
                deposited_at = datetime.fromisoformat(deposited_at)
            except Exception:
                deposited_at = None
        
        if deposited_at and isinstance(deposited_at, datetime):
            days_passed = (datetime.now(timezone.utc) - deposited_at).days
            interest = int(base_balance * 0.10 * days_passed)
        else:
            interest = 0
        
        total = base_balance + interest
        
        # ✅ Обновляем баланс
        current_balance = user.get("score_balance", 0)
        user["score_balance"] = current_balance + total
        
        bank_data["balance"] = 0
        bank_data["deposited_at"] = None
        user["bank_data"] = bank_data
        
        self.storage.save_user(user_id, user)
        logger.info(f"📊 Баланс после снятия: {user['score_balance']}")
        
        # ✅ ПРОВЕРКА
        test_user = self.storage.get_user(user_id)
        test_bank = self._get_bank_data(test_user) if test_user else {}
        logger.info(f"🔍 ПРОВЕРКА: после снятия баланс в банке = {test_bank.get('balance')}")
        
        message = f"✅ Забрано {total} золотых! (вклад: {base_balance}, проценты: {interest})"
        return True, message, total