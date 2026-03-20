# core/artifact_manager.py
"""
Менеджер артефактов — прокачка, эффекты, баланс.
Версия: 1.1 (Fix: ARTIFACT_CONFIG Keys) 🔮✅
"""

import logging
from typing import Dict, Any, Tuple, Optional
from database.storage import PlayerStorage

logger = logging.getLogger(__name__)

# ✅ ВСТРОЕННАЯ КОНФИГУРАЦИЯ (не зависит от items.py)
ARTIFACT_CONFIG = {
    "artifact_luck": {
        "name": "🍀 Артефакт Удачи",
        "base_price": 500,
        "effect": "score_bonus",
        "base_value": 0.05,
        "per_level": 0.05,
        "max_level": 10,
        "max_value": 0.40,
        "cost_multiplier": 1.4,
        "requires_upkeep": True
    },
    "artifact_power": {
        "name": "⚡ Артефакт Силы",
        "base_price": 500,
        "effect": "penalty_reduction",
        "base_value": 0.10,
        "per_level": 0.10,
        "max_level": 10,
        "max_value": 0.75,
        "min_penalty": 2,
        "cost_multiplier": 1.4,
        "requires_upkeep": True
    },
    "artifact_wisdom": {
        "name": "🧠 Артефакт Мудрости",
        "base_price": 750,
        "effect": "boss_hints",
        "base_value": 1,
        "per_level": 1,
        "max_level": 10,
        "max_value": 10,
        "max_per_battle": 3,
        "cost_multiplier": 1.45,
        "requires_upkeep": True
    },
}


class ArtifactManager:
    """Управление артефактами игрока"""
    
    def __init__(self, storage: PlayerStorage, castle_engine=None):
        self.storage = storage
        self.castle_engine = castle_engine
        logger.info("✅ ArtifactManager инициализирован")
    
    def _get_user_artifacts(self, user_id: str) -> Dict[str, int]:
        """Получает словарь {artifact_id: level}"""
        user = self.storage.get_user(user_id)
        if not user:
            return {}
        return user.get("artifact_upgrades", {})
    
    def get_artifact_level(self, user_id: str, artifact_id: str) -> int:
        """Получает уровень артефакта"""
        artifacts = self._get_user_artifacts(user_id)
        return artifacts.get(artifact_id, 0)
    
    def get_upgrade_cost(self, artifact_id: str, current_level: int) -> int:
        """Считает стоимость следующего уровня"""
        if artifact_id not in ARTIFACT_CONFIG:
            return 0
        
        config = ARTIFACT_CONFIG[artifact_id]
        if current_level >= config["max_level"]:
            return 0  # Максимальный уровень
        
        # Формула: base_price × multiplier^level
        cost = int(config["base_price"] * (config["cost_multiplier"] ** current_level))
        return cost
    
    def get_effect_value(self, artifact_id: str, level: int) -> float:
        """Получает значение эффекта для уровня с учётом капа"""
        if artifact_id not in ARTIFACT_CONFIG:
            return 0.0
        
        config = ARTIFACT_CONFIG[artifact_id]
        value = config["base_value"] + (config["per_level"] * (level - 1))
        return min(value, config["max_value"])  # ⚠️ КАП!
    
    def is_upkeep_active(self, user_id: str) -> bool:
        """Проверяет, оплачен ли upkeep замка"""
        if not self.castle_engine:
            logger.warning("⚠️ CastleEngine не инициализирован, предполагаем upkeep активен")
            return True
        
        castle_state = self.castle_engine.get_castle_state(user_id)
        return castle_state.get("bonuses_active", False)
    
    def can_upgrade(self, user_id: str, artifact_id: str) -> Tuple[bool, str, int]:
        """
        Проверяет, можно ли улучшить артефакт.
        
        Returns:
            (can_upgrade: bool, message: str, cost: int)
        """
        if artifact_id not in ARTIFACT_CONFIG:
            return False, "❌ Артефакт не найден", 0
        
        user = self.storage.get_user(user_id)
        if not user:
            return False, "❌ Игрок не найден", 0
        
        current_level = self.get_artifact_level(user_id, artifact_id)
        config = ARTIFACT_CONFIG[artifact_id]
        
        if current_level >= config["max_level"]:
            return False, "⚠️ Артефакт уже максимального уровня!", 0
        
        cost = self.get_upgrade_cost(artifact_id, current_level)
        balance = user.get("score_balance", 0)
        
        if balance < cost:
            return False, f"❌ Недостаточно золота! Нужно {cost:,}, есть {balance:,}", cost
        
        return True, f"✅ Можно улучшить за {cost:,} золотых", cost
    
    def upgrade_artifact(self, user_id: str, artifact_id: str) -> Tuple[bool, str]:
        """
        Улучшает артефакт.
        
        Returns:
            (success: bool, message: str)
        """
        if artifact_id not in ARTIFACT_CONFIG:
            return False, "❌ Артефакт не найден"
        
        user = self.storage.get_user(user_id)
        if not user:
            return False, "❌ Игрок не найден"
        
        can_upgrade, message, cost = self.can_upgrade(user_id, artifact_id)
        if not can_upgrade:
            return False, message
        
        # Списываем золото
        user["score_balance"] -= cost
        
        # Обновляем уровень
        if "artifact_upgrades" not in user:
            user["artifact_upgrades"] = {}
        
        current_level = user["artifact_upgrades"].get(artifact_id, 0)
        user["artifact_upgrades"][artifact_id] = current_level + 1
        
        # Сохраняем
        self.storage.save_user(user_id, user)
        
        new_level = current_level + 1
        effect_value = self.get_effect_value(artifact_id, new_level)
        
        logger.info(f"🔮 Артефакт {artifact_id} улучшен до уровня {new_level} (эффект: {effect_value})")
        
        config = ARTIFACT_CONFIG[artifact_id]
        effect_desc = self._format_effect(artifact_id, effect_value, config)
        
        return True, f"✅ {config['name']} улучшен до уровня {new_level}!\n📊 Эффект: {effect_desc}"
    
    def _format_effect(self, artifact_id: str, value: float, config: Dict) -> str:
        """Форматирует описание эффекта"""
        if artifact_id == "artifact_luck":
            return f"+{int(value * 100)}% к очкам за задачу"
        elif artifact_id == "artifact_power":
            min_penalty = config.get("min_penalty", 1)
            return f"-{int(value * 100)}% штрафа (мин. -{min_penalty} очка)"
        elif artifact_id == "artifact_wisdom":
            max_per_battle = config.get("max_per_battle", 3)
            return f"+{int(value)} подсказок (макс. {max_per_battle} за бой)"
        return f"Эффект: {value}"
    
    def get_all_artifacts(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Получает все артефакты игрока с уровнями"""
        user = self.storage.get_user(user_id)
        if not user:
            return {}
        
        artifacts = user.get("artifact_upgrades", {})
        upkeep_active = self.is_upkeep_active(user_id)
        
        result = {}
        
        for artifact_id, config in ARTIFACT_CONFIG.items():
            level = artifacts.get(artifact_id, 0)
            effect_value = self.get_effect_value(artifact_id, level)
            next_cost = self.get_upgrade_cost(artifact_id, level)
            
            result[artifact_id] = {
                "name": config["name"],
                "level": level,
                "max_level": config["max_level"],
                "effect": self._format_effect(artifact_id, effect_value, config),
                "next_upgrade_cost": next_cost if level < config["max_level"] else None,
                "is_maxed": level >= config["max_level"],
                "is_active": upkeep_active if config.get("requires_upkeep", False) else True
            }
        
        return result
    
    def apply_score_bonus(self, user_id: str, base_score: int) -> int:
        """
        Применяет бонус от Артефакта Удачи.
        
        ⚠️ Работает ТОЛЬКО если upkeep оплачен!
        """
        level = self.get_artifact_level(user_id, "artifact_luck")
        if level == 0:
            return base_score
        
        # Проверяем upkeep
        if not self.is_upkeep_active(user_id):
            logger.info(f"⚠️ Артефакт Удачи не активен: upkeep не оплачен (user_id={user_id})")
            return base_score
        
        bonus_multiplier = self.get_effect_value("artifact_luck", level)
        bonus = int(base_score * bonus_multiplier)
        final_score = base_score + bonus
        
        logger.debug(f"🍀 Удача: {base_score} + {bonus} = {final_score} (уровень {level})")
        
        return final_score
    
    def apply_penalty_reduction(self, user_id: str, base_penalty: int) -> int:
        """
        Применяет снижение штрафа от Артефакта Силы.
        
        ⚠️ Работает ТОЛЬКО если upkeep оплачен!
        ⚠️ Всегда остаётся минимальный штраф!
        """
        level = self.get_artifact_level(user_id, "artifact_power")
        if level == 0:
            return base_penalty
        
        # Проверяем upkeep
        if not self.is_upkeep_active(user_id):
            logger.info(f"⚠️ Артефакт Силы не активен: upkeep не оплачен (user_id={user_id})")
            return base_penalty
        
        config = ARTIFACT_CONFIG["artifact_power"]
        reduction = self.get_effect_value("artifact_power", level)
        min_penalty = config.get("min_penalty", 1)
        
        # Считаем сниженный штраф
        reduced_penalty = int(abs(base_penalty) * (1 - reduction))
        
        # ⚠️ Применяем минимум!
        final_penalty = max(reduced_penalty, min_penalty)
        
        # Сохраняем знак (штраф отрицательный)
        final_penalty = -abs(final_penalty)
        
        logger.debug(f"⚡ Сила: {base_penalty} → {final_penalty} (уровень {level}, снижение {int(reduction*100)}%)")
        
        return final_penalty
    
    def get_boss_hints(self, user_id: str) -> int:
        """
        Получает количество подсказок для боя с боссом.
        
        ⚠️ Работает ТОЛЬКО если upkeep оплачен!
        """
        level = self.get_artifact_level(user_id, "artifact_wisdom")
        if level == 0:
            return 0
        
        # Проверяем upkeep
        if not self.is_upkeep_active(user_id):
            logger.info(f"⚠️ Артефакт Мудрости не активен: upkeep не оплачен (user_id={user_id})")
            return 0
        
        config = ARTIFACT_CONFIG["artifact_wisdom"]
        hints = int(self.get_effect_value("artifact_wisdom", level))
        max_per_battle = config.get("max_per_battle", 3)
        
        # ⚠️ Ограничиваем максимум за бой
        return min(hints, max_per_battle)