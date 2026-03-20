# core/castle_engine.py
"""
Движок замка — декорации, upkeep, бонусы.
Версия: 2.2 (Fix: JSON Parse in get_decoration_level) 🏰✨✅
"""

import logging
import sqlite3
import json
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from database.storage import PlayerStorage
from items import CASTLE_DECORATIONS

logger = logging.getLogger(__name__)


def _parse_decoration_upgrades(data):
    """
    ✅ Универсальная функция для парсинга decoration_upgrades.
    Работает и со строкой (JSON), и с dict.
    """
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except:
            return {}
    return {}


class CastleEngine:
    """Управление замком игрока"""
    
    def __init__(self, storage: PlayerStorage):
        self.storage = storage
        logger.info("✅ CastleEngine инициализирован")
    
    def get_castle_state(self, user_id: str) -> Dict[str, Any]:
        """Получает состояние замка игрока"""
        user = self.storage.get_user(user_id)
        if not user:
            return {"error": "Игрок не найден"}
        
        # Получаем данные замка
        castle_data = user.get("castle_data", {})
        upkeep_paid_until = castle_data.get("upkeep_paid_until", 0)
        
        # ✅ КОНВЕРТИРУЕМ СТРОКУ В FLOAT (если это строка)
        if isinstance(upkeep_paid_until, str):
            try:
                upkeep_paid_until = float(upkeep_paid_until)
            except (ValueError, TypeError):
                upkeep_paid_until = 0
        
        # Проверяем upkeep
        now = datetime.now(timezone.utc).timestamp()
        bonuses_active = upkeep_paid_until > now
        
        # Получаем уровни декораций
        decoration_upgrades = _parse_decoration_upgrades(user.get("decoration_upgrades", {}))
        
        # Считаем общий бонус
        total_bonus = self._calculate_total_bonus(decoration_upgrades, bonuses_active)
        
        return {
            "upkeep_paid_until": upkeep_paid_until,
            "bonuses_active": bonuses_active,
            "days_remaining": max(0, int((upkeep_paid_until - now) / 86400)) if upkeep_paid_until > 0 else 0,
            "decoration_upgrades": decoration_upgrades,
            "total_bonus": total_bonus,
            "total_bonus_display": f"+{int(total_bonus * 100)}%" if bonuses_active else "❌ Не активно (upkeep)"
        }
    
    def _calculate_total_bonus(self, decoration_upgrades: Dict[str, int], bonuses_active: bool) -> float:
        """Считает общий бонус от всех декораций"""
        if not bonuses_active:
            return 0.0
        
        total_bonus = 0.0
        
        for dec in CASTLE_DECORATIONS:
            dec_id = dec["id"]
            level = decoration_upgrades.get(dec_id, 0)
            
            if level > 0:
                # Бонус = base + (per_level × (level - 1)), но не больше max_bonus
                bonus = dec["bonus_per_level"] + (dec["bonus_per_level"] * (level - 1))
                bonus = min(bonus, dec["max_bonus"])
                total_bonus += bonus
        
        return total_bonus
    
    def get_decoration_level(self, user_id: str, decoration_id: str) -> int:
        """Получает уровень декорации"""
        user = self.storage.get_user(user_id)
        if not user:
            return 0
        
        # ✅ ПАРСИМ JSON СТРОКУ!
        decoration_upgrades = _parse_decoration_upgrades(user.get("decoration_upgrades", {}))
        return decoration_upgrades.get(decoration_id, 0)
    
    def get_decoration_bonus(self, decoration_id: str, level: int) -> float:
        """Получает бонус декорации на уровне"""
        dec_config = None
        for dec in CASTLE_DECORATIONS:
            if dec["id"] == decoration_id:
                dec_config = dec
                break
        
        if not dec_config:
            return 0.0
        
        if level == 0:
            return 0.0
        
        bonus = dec_config["bonus_per_level"] + (dec_config["bonus_per_level"] * (level - 1))
        return min(bonus, dec_config["max_bonus"])
    
    def get_upgrade_cost(self, decoration_id: str, current_level: int) -> int:
        """Считает стоимость следующего уровня"""
        dec_config = None
        for dec in CASTLE_DECORATIONS:
            if dec["id"] == decoration_id:
                dec_config = dec
                break
        
        if not dec_config:
            return 0
        
        if current_level >= dec_config["max_level"]:
            return 0  # Максимальный уровень
        
        # Формула: base_price × multiplier^level
        cost = int(dec_config["base_price"] * (dec_config["cost_multiplier"] ** current_level))
        return cost
    
    def upgrade_decoration(self, user_id: str, decoration_id: str) -> Tuple[bool, str]:
        """
        Улучшить декорацию (покупка = улучшение).
        ✅ ПРЯМОЕ ОБНОВЛЕНИЕ БАЗЫ!
        """
        # Находим конфигурацию
        dec_config = None
        for dec in CASTLE_DECORATIONS:
            if dec["id"] == decoration_id:
                dec_config = dec
                break
        
        if not dec_config:
            return (False, "❌ Декорация не найдена")
        
        # Получаем текущего пользователя
        user = self.storage.get_user(user_id)
        if not user:
            return (False, "❌ Игрок не найден")
        
        current_level = self.get_decoration_level(user_id, decoration_id)
        
        # Проверяем макс уровень
        if current_level >= dec_config["max_level"]:
            return (False, f"⚠️ {dec_config['name']} уже максимального уровня ({dec_config['max_level']})!")
        
        # Считаем стоимость
        cost = self.get_upgrade_cost(decoration_id, current_level)
        
        # Проверяем баланс
        balance = user.get("score_balance", 0)
        if balance < cost:
            return (False, f"❌ Недостаточно золота! Нужно {cost:,}, есть {balance:,}")
        
        # Списываем золото через ScoreManager
        from core.score_manager import ScoreManager
        score_manager = ScoreManager(self.storage)
        success, message = score_manager.spend_score(
            user_id=user_id,
            amount=cost,
            reason="decoration_upgrade"
        )
        
        if not success:
            return (False, message)
        
        # ✅ ПРЯМО ОБНОВЛЯЕМ decoration_upgrades В БАЗЕ!
        conn = sqlite3.connect("data/progress.db")
        c = conn.cursor()
        
        # Получаем текущие уровни
        c.execute("SELECT decoration_upgrades FROM users WHERE user_id = ?", (str(user_id),))
        row = c.fetchone()
        
        current_upgrades = _parse_decoration_upgrades(row[0] if row else {})
        
        # Обновляем уровень
        new_level = current_level + 1
        current_upgrades[decoration_id] = new_level
        
        # Сохраняем в базу
        c.execute(
            "UPDATE users SET decoration_upgrades = ? WHERE user_id = ?",
            (json.dumps(current_upgrades, ensure_ascii=False), str(user_id))
        )
        conn.commit()
        conn.close()
        
        new_bonus = self.get_decoration_bonus(decoration_id, new_level)
        
        logger.info(f"🏰 Декорация {decoration_id} улучшена до уровня {new_level} (бонус: +{int(new_bonus * 100)}%)")
        
        return (True, f"✅ {dec_config['name']} улучшена до уровня {new_level}!\n📊 Бонус: +{int(new_bonus * 100)}% к очкам\n💰 Списано: {cost:,} золотых")
    
    def add_decoration(self, user_id: str, decoration_id: str, name: str) -> Tuple[bool, str]:
        """
        Устаревший метод для обратной совместимости.
        ✅ Теперь вызывает upgrade_decoration()
        """
        return self.upgrade_decoration(user_id, decoration_id)
    
    def pay_upkeep(self, user_id: str, days: int = 1) -> Tuple[bool, str]:
        """Оплатить содержание замка"""
        user = self.storage.get_user(user_id)
        if not user:
            return (False, "❌ Игрок не найден")
        
        # Стоимость: 50 золота в день
        cost = 50 * days
        
        balance = user.get("score_balance", 0)
        if balance < cost:
            return (False, f"❌ Недостаточно золота! Нужно {cost:,}, есть {balance:,}")
        
        # Списываем золото
        from core.score_manager import ScoreManager
        score_manager = ScoreManager(self.storage)
        success, message = score_manager.spend_score(
            user_id=user_id,
            amount=cost,
            reason="castle_upkeep"
        )
        
        if not success:
            return (False, message)
        
        # Обновляем upkeep_paid_until
        castle_data = user.get("castle_data", {})
        now = datetime.now(timezone.utc).timestamp()
        
        # Если upkeep уже оплачен — добавляем дни к текущей дате
        current_paid_until = castle_data.get("upkeep_paid_until", 0)
        
        # ✅ КОНВЕРТИРУЕМ СТРОКУ В FLOAT
        if isinstance(current_paid_until, str):
            try:
                current_paid_until = float(current_paid_until)
            except (ValueError, TypeError):
                current_paid_until = 0
        
        if current_paid_until > now:
            new_paid_until = current_paid_until + (days * 86400)
        else:
            new_paid_until = now + (days * 86400)
        
        castle_data["upkeep_paid_until"] = new_paid_until
        user["castle_data"] = castle_data
        self.storage.save_user(user_id, user)
        
        logger.info(f"🏰 Upkeep оплачен: user_id={user_id}, days={days}, until={new_paid_until}")
        
        return (True, f"✅ Содержание замка оплачено на {days} дн.!\n💰 Списано: {cost:,} золотых\n🎁 Бонусы активны!")
    
    def get_total_castle_bonus(self, user_id: str) -> float:
        """Получает общий бонус замка (с учётом upkeep)"""
        castle_state = self.get_castle_state(user_id)
        return castle_state.get("total_bonus", 0.0)