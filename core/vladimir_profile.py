# core/vladimir_profile.py
"""
Профиль игрока — для Владимира, Тайной комнаты и динамической сложности.
Версия: 1.1 (Secret Room DB Sync Fix) 🎩🗝️💾✅
"""

import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PlayerProfile:
    """
    Единый профиль игрока для всех систем.
    Хранится в user_data["player_profile"]
    """
    
    # Пороги для реакций Владимира
    THRESHOLD_HIGH = 70
    THRESHOLD_MEDIUM = 50
    
    # Шанс мистической фразы
    MYSTERY_CHANCE = 0.03
    
    # Минимальный интервал между комментариями (сек)
    MIN_COMMENT_INTERVAL = 300
    
    # Лимит попыток в Тайной комнате в день
    SECRET_ROOM_MAX_ATTEMPTS = 3
    
    def __init__(self, user_data: dict):
        self.user_data = user_data
        # ✅ ВАЖНО: Берём ссылку на player_profile внутри user_data
        if "player_profile" not in user_data:
            user_data["player_profile"] = {
                "greed": 0, "risk": 0, "logic": 0, "persistence": 0, "creativity": 0,
                "boss_stats": {"bosses_defeated": [], "attempts_per_boss": {}, "final_boss_attempts": 0, "best_accuracy": 0.0},
                "difficulty_profile": {"avg_accuracy": 0.0, "avg_response_time": 0.0, "hint_usage": 0, "streak_best": 0, "streak_current": 0},
                "secret_room": {"attempts_today": 0, "last_visit": None, "last_visit_date": None, "total_visits": 0, "streak": 0, "lore_seen": []},
                "weaknesses": {}, "strengths": {},
                "last_comment": 0, "mystery_unlocked": False, "comment_count": 0,
            }
        self.profile = user_data["player_profile"]  # ← ССЫЛКА, не копия!
    
    # ==================== ОТСЛЕЖИВАНИЕ ПОВЕДЕНИЯ ====================
    
    def track_purchase(self, amount: int):
        """Отслеживает покупку — увеличивает жадность."""
        if amount >= 1000:
            self.profile["greed"] = min(100, self.profile["greed"] + 15)
        elif amount >= 500:
            self.profile["greed"] = min(100, self.profile["greed"] + 10)
        elif amount >= 100:
            self.profile["greed"] = min(100, self.profile["greed"] + 5)
        self._decay("greed")
    
    def track_risky_choice(self):
        """Рискованный выбор (угадывание, быстрые ответы)."""
        self.profile["risk"] = min(100, self.profile["risk"] + 10)
        self._decay("risk")
    
    def track_logical_choice(self):
        """Логичный выбор (правильные ответы, обдуманные решения)."""
        self.profile["logic"] = min(100, self.profile["logic"] + 10)
        self._decay("logic")
    
    def track_persistence(self):
        """Игрок продолжает после неудачи."""
        self.profile["persistence"] = min(100, self.profile["persistence"] + 15)
        self._decay("persistence")
    
    def _decay(self, stat: str):
        """Постепенно снижает показатель."""
        self.profile[stat] = max(0, self.profile[stat] - 2)
    
    # ==================== БОССЫ ====================
    
    def track_boss_attempt(self, boss_id: str, won: bool, accuracy: float):
        """Отслеживает попытку босса."""
        boss_stats = self.profile["boss_stats"]
        
        if boss_id not in boss_stats["attempts_per_boss"]:
            boss_stats["attempts_per_boss"][boss_id] = 0
        boss_stats["attempts_per_boss"][boss_id] += 1
        
        if won:
            if boss_id not in boss_stats["bosses_defeated"]:
                boss_stats["bosses_defeated"].append(boss_id)
            if accuracy > boss_stats["best_accuracy"]:
                boss_stats["best_accuracy"] = accuracy
            self.profile["difficulty_profile"]["streak_current"] += 1
            if self.profile["difficulty_profile"]["streak_current"] > self.profile["difficulty_profile"]["streak_best"]:
                self.profile["difficulty_profile"]["streak_best"] = self.profile["difficulty_profile"]["streak_current"]
        else:
            self.profile["difficulty_profile"]["streak_current"] = 0
            self.profile["persistence"] = min(100, self.profile["persistence"] + 10)
        
        if boss_id == "final_boss" and not won:
            boss_stats["final_boss_attempts"] += 1
    
    def track_weakness(self, topic: str):
        """Отслеживает слабую тему."""
        weaknesses = self.profile.setdefault("weaknesses", {})
        weaknesses[topic] = weaknesses.get(topic, 0) + 1
        for t in list(weaknesses.keys()):
            weaknesses[t] = max(0, weaknesses[t] - 1)
    
    def track_strength(self, topic: str):
        """Отслеживает сильную тему."""
        strengths = self.profile.setdefault("strengths", {})
        strengths[topic] = strengths.get(topic, 0) + 1
    
    # ==================== ДИНАМИЧЕСКАЯ СЛОЖНОСТЬ ====================
    
    def track_accuracy(self, accuracy: float):
        """Обновляет среднюю точность."""
        diff = self.profile["difficulty_profile"]
        current = diff["avg_accuracy"]
        count = self.profile.get("total_tasks", 0) + 1
        diff["avg_accuracy"] = (current * count + accuracy) / (count + 1)
        self.profile["total_tasks"] = count
    
    def track_hint_used(self):
        """Игрок использовал подсказку."""
        self.profile["difficulty_profile"]["hint_usage"] += 1
    
    def get_difficulty_hints(self) -> dict:
        """Возвращает модификаторы сложности."""
        diff = self.profile["difficulty_profile"]
        boss_stats = self.profile["boss_stats"]
        
        hints = {
            "extra_time": 10,
            "hints_allowed": True,
            "boss_health": 5,
            "boss_special": False,
            "penalty_reduction": 0,
        }
        
        if boss_stats.get("final_boss_attempts", 0) >= 5:
            hints["extra_time"] += 20
            hints["boss_health"] -= 1
            hints["hints_allowed"] = True
        
        if diff["avg_accuracy"] >= 0.8:
            hints["extra_time"] -= 5
            hints["boss_health"] += 1
            hints["boss_special"] = True
        
        if diff["hint_usage"] >= 10:
            hints["hints_allowed"] = True
            hints["extra_time"] += 5
        
        if diff["streak_current"] >= 5:
            hints["boss_special"] = True
        
        if diff["avg_accuracy"] < 0.5:
            hints["penalty_reduction"] = 50
        
        return hints
    
    # ==================== ТАЙНАЯ КОМНАТА: ЕЖЕДНЕВНЫЙ ДОСТУП ====================
    
    def get_secret_room_status(self) -> dict:
        """Возвращает статус доступа к Тайной комнате."""
        now = datetime.now(timezone.utc)
        secret = self.profile.setdefault("secret_room", {})
        
        last_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_visit = secret.get("last_visit")
        
        if isinstance(last_visit, str):
            try:
                last_visit = datetime.fromisoformat(last_visit.replace('Z', '+00:00')).timestamp()
            except:
                last_visit = 0
        elif last_visit is None:
            last_visit = 0
        
        # ✅ СБРОС ПОПЫТОК ЕСЛИ НОВЫЙ ДЕНЬ
        if last_visit < last_reset.timestamp():
            secret["attempts_today"] = 0
            secret["last_visit"] = now.isoformat()
        
        attempts_left = max(0, self.SECRET_ROOM_MAX_ATTEMPTS - secret.get("attempts_today", 0))
        
        streak = secret.get("streak", 0)
        last_date = secret.get("last_visit_date")
        today = now.date().isoformat()
        yesterday = (now.date() - timedelta(days=1)).isoformat()
        
        if last_date == yesterday:
            streak += 1
        elif last_date != today:
            streak = 1
        
        next_reset = last_reset + timedelta(days=1)
        seconds_left = (next_reset - now).total_seconds()
        hours_left = int(seconds_left // 3600)
        minutes_left = int((seconds_left % 3600) // 60)
        
        return {
            "available": attempts_left > 0,
            "attempts_left": attempts_left,
            "resets_at": f"{hours_left}ч {minutes_left}м",
            "streak": streak,
            "total_visits": secret.get("total_visits", 0),
        }
    
    def track_secret_room_visit(self, lore_seen: List[str] = None):
        """Отслеживает посещение Тайной комнаты."""
        secret = self.profile.setdefault("secret_room", {})
        now = datetime.now(timezone.utc)
        
        secret["attempts_today"] = secret.get("attempts_today", 0) + 1
        secret["last_visit"] = now.isoformat()
        secret["last_visit_date"] = now.date().isoformat()
        secret["total_visits"] = secret.get("total_visits", 0) + 1
        
        if lore_seen:
            seen_lore = secret.setdefault("lore_seen", [])
            for lore_id in lore_seen:
                if lore_id not in seen_lore:
                    seen_lore.append(lore_id)
        
        yesterday = (now.date() - timedelta(days=1)).isoformat()
        if secret.get("last_visit_date") == yesterday:
            secret["streak"] = secret.get("streak", 0) + 1
        elif secret.get("last_visit_date") != now.date().isoformat():
            secret["streak"] = 1
        
        # ✅ ВАЖНО: Не вызываем self.save() здесь!
        # Это делает explore_secret_room() после track_secret_room_visit()
    
    # ==================== ЛОР-СИСТЕМА ====================
    
    def get_available_lore(self, category: str = None, limit: int = 2) -> List[dict]:
        """Возвращает доступные лор-записи (случайные, непрочитанные)."""
        import json
        import os
        
        secret = self.profile.setdefault("secret_room", {})
        seen_lore = set(secret.get("lore_seen", []))
        
        # Загружаем лор из файла
        lore_file = os.path.join("data", "secret_lore.json")
        if not os.path.exists(lore_file):
            return []
        
        try:
            with open(lore_file, "r", encoding="utf-8") as f:
                all_lore = json.load(f).get("lore_entries", [])
        except:
            return []
        
        # Фильтруем
        player_level = self.profile.get("level", 1)
        available = [
            lore for lore in all_lore
            if lore["id"] not in seen_lore
            and lore.get("unlock_level", 1) <= player_level
            and (category is None or lore["category"] == category)
        ]
        
        if not available:
            return []
        
        return random.sample(available, min(limit, len(available)))
    
    def mark_lore_seen(self, lore_id: str):
        """Отмечает лор как прочитанный."""
        secret = self.profile.setdefault("secret_room", {})
        seen = secret.setdefault("lore_seen", [])
        if lore_id not in seen:
            seen.append(lore_id)
        self.save()
    
    def get_lore_completion(self) -> dict:
        """Возвращает прогресс сбора лора."""
        secret = self.profile.setdefault("secret_room", {})
        seen = len(secret.get("lore_seen", []))
        total = 30
        
        return {
            "seen": seen,
            "total": total,
            "percent": round(seen / total * 100) if total > 0 else 0,
            "reward_unlocked": seen == total,
        }
    
    # ==================== КОММЕНТАРИИ ВЛАДИМИРА ====================
    
    def should_comment(self) -> bool:
        """Проверяет стоит ли Владимиру комментировать."""
        now = datetime.now(timezone.utc).timestamp()
        last = self.profile.get("last_comment", 0)
        
        if now - last < self.MIN_COMMENT_INTERVAL:
            return False
        
        if random.random() < self.MYSTERY_CHANCE:
            return True
        
        if (self.profile["greed"] >= self.THRESHOLD_HIGH or
            self.profile["risk"] >= self.THRESHOLD_HIGH or
            self.profile["logic"] >= self.THRESHOLD_HIGH):
            return True
        
        return False
    
    def get_comment(self) -> dict:
        """Возвращает комментарий Владимира."""
        self.profile["last_comment"] = datetime.now(timezone.utc).timestamp()
        self.profile["comment_count"] = self.profile.get("comment_count", 0) + 1
        
        # Мистическая фраза
        if random.random() < self.MYSTERY_CHANCE:
            self.profile["mystery_unlocked"] = True
            return {
                "text": random.choice([
                    "«Тайна замка… она всё более странная…»",
                    "«Не все двери ведут туда, куда должны…»",
                    "«Числа шепчут… слышите?»",
                    "«Владимир смотрит на вас дольше обычного…»"
                ]),
                "mood": "mysterious",
                "trigger": "mystery"
            }
        
        # Жадность
        if self.profile["greed"] >= self.THRESHOLD_HIGH:
            return {
                "text": random.choice([
                    "«Опять покупки? Казначей уже нервничает…»",
                    "«Золото не приносит счастья. Но я не судья.»",
                    "«Ваша коллекция растёт… как и счета за хранение.»"
                ]),
                "mood": "disapprove",
                "trigger": "greed"
            }
        
        # Риск
        if self.profile["risk"] >= self.THRESHOLD_HIGH:
            return {
                "text": random.choice([
                    "«Осторожнее. Азарт затмевает разум.»",
                    "«Владимир обеспокоен вашими решениями…»",
                    "«Риск — благородное дело. Но не всегда.»"
                ]),
                "mood": "thinking",
                "trigger": "risk"
            }
        
        # Логика
        if self.profile["logic"] >= self.THRESHOLD_HIGH:
            return {
                "text": random.choice([
                    "«Разумный выбор. Я горжусь.»",
                    "«Вот это я понимаю — стратегия!»",
                    "«Ваша логика безупречна. Так держать.»"
                ]),
                "mood": "approve",
                "trigger": "logic"
            }
        
        # Нейтральная фраза
        return {
            "text": random.choice([
                "«Чай, сударыня?»",
                "«Всё в порядке?»",
                "«Владимир к вашим услугам.»"
            ]),
            "mood": "calm",
            "trigger": "neutral"
        }
    
    def get_boss_intro(self, boss_id: str) -> str:
        """Возвращает вступительную фразу босса."""
        logic = self.profile["logic"]
        risk = self.profile["risk"]
        persistence = self.profile["persistence"]
        attempts = self.profile["boss_stats"]["final_boss_attempts"]
        
        if boss_id == "final_boss":
            if attempts >= 5:
                return "«Снова ты... Упрямство достойно уважения. Но не победы.»"
            elif logic >= 70:
                return "«Вижу... ты силён разумом. Но разум ломается.»"
            elif risk >= 70:
                return "«Азартный? Опасно. Азарт сжигает.»"
            elif persistence >= 70:
                return "«Упрямый... Уважаю. Но упрямство не спасёт.»"
            else:
                return "«Ты... как все. Исчезни.»"
        return "«Сразимся?»"
    
    def get_vladimir_boss_comment(self, boss_id: str, before_boss: bool) -> str:
        """Комментарий Владимира перед/после босса."""
        if before_boss:
            if boss_id == "final_boss":
                logic_val = self.profile["logic"]
                return (
                    f"«Вы справились с шестью... Но Он — другой.\n"
                    f"Я видел тех, кто возвращался. Они... изменились.\n\n"
                    f"💡 Ваша логика ({logic_val}/100) поможет в этом бою!»"
                )
            return "«Осторожнее. Этот босс силён.»"
        else:
            if boss_id == "final_boss":
                return (
                    "«Вы... победили Его? Я не верил.\n"
                    "Простите мою дерзость.\n"
                    "Замок — ваш. И я тоже. В смысле... к вашим услугам.»"
                )
            return "«Победа! Владимир гордится.»"
    
    # ==================== СОХРАНЕНИЕ ====================
    
    def save(self):
        """Сохраняет профиль в user_data (уже ссылка, так что ничего делать не нужно)."""
        # ✅ self.profile ЭТО ССЫЛКА на user_data["player_profile"]
        # Так что изменения уже в user_data!
        pass
    
    def get_profile_summary(self) -> str:
        """Возвращает краткую сводку для отладки."""
        greed_val = self.profile["greed"]
        risk_val = self.profile["risk"]
        logic_val = self.profile["logic"]
        persistence_val = self.profile["persistence"]
        bosses_count = len(self.profile["boss_stats"]["bosses_defeated"])
        accuracy_val = self.profile["difficulty_profile"]["avg_accuracy"]
        
        return (
            f"🎩 Профиль игрока:\n"
            f"💰 Жадность: {greed_val}/100\n"
            f"🎲 Риск: {risk_val}/100\n"
            f"🧠 Логика: {logic_val}/100\n"
            f"💪 Упорство: {persistence_val}/100\n"
            f"⚔️ Боссов побеждено: {bosses_count}\n"
            f"📈 Точность: {accuracy_val:.1%}"
        )