# core/difficulty_manager.py
"""
Менеджер динамической сложности задач.
Версия: 1.0 (MVP Stub)

Пока — базовая реализация. Позже добавим:
- Адаптацию по точности
- 5 уровней сложности
- Реплики персонажей
"""

from typing import Tuple, Optional
from database.storage import PlayerStorage

class DifficultyManager:
    """Управляет сложностью задач для игрока"""
    
    def __init__(self, storage: PlayerStorage):
        self.storage = storage
    
    def get_current_level(self, user_id: str, island_id: str) -> int:
        """Получает текущий уровень сложности для острова"""
        user = self.storage.get_user(user_id)
        if not user:
            return 1
        
        key = f"difficulty_{island_id}"
        return user.get(key, 1)
    
    def get_score_multiplier(self, user_id: str, task_id: str) -> float:
        """Возвращает множитель очков в зависимости от уровня"""
        # Извлекаем island_id из task_id (например, "addition_level_3" → "addition")
        island_id = task_id.split("_")[0] if "_" in task_id else "addition"
        level = self.get_current_level(user_id, island_id)
        
        # Множители по уровням (MVP)
        multipliers = {
            1: 1.0,  # Разминка
            2: 1.2,  # Нормально
            3: 1.5,  # Вызов
            4: 1.8,  # Эксперт
            5: 2.0,  # Матемаг
        }
        
        return multipliers.get(level, 1.0)
    
    def adjust_level(self, user_id: str, island_id: str, is_correct: bool, consecutive_correct: int) -> Tuple[int, str]:
        """
        Корректирует уровень сложности.
        
        Правила (MVP):
        - 2 правильных подряд → +1 уровень
        - 2 неправильных подряд → -1 уровень
        - Минимум 3 задачи на уровне перед повышением
        
        Returns:
            (new_level, change_type) где change_type: "level_up", "level_down", "same"
        """
        current_level = self.get_current_level(user_id, island_id)
        new_level = current_level
        change = "same"
        
        # Получаем статистику по задачам на этом уровне
        tasks_on_level = self._get_tasks_count_on_level(user_id, island_id, current_level)
        
        if is_correct:
            # Повышение: 2 правильных подряд + минимум 3 задачи на уровне
            if consecutive_correct >= 2 and tasks_on_level >= 3 and current_level < 5:
                new_level = current_level + 1
                change = "level_up"
        else:
            # Понижение: 2 неправильных подряд
            if consecutive_correct == 0 and current_level > 1:
                # Проверяем, была ли ошибка до этого (хранится в game_state)
                user = self.storage.get_user(user_id)
                if user and user.get("game_state", {}).get(f"last_error_{island_id}", False):
                    new_level = current_level - 1
                    change = "level_down"
        
        # Сохраняем новый уровень, если изменился
        if new_level != current_level:
            self._save_level(user_id, island_id, new_level)
        
        return new_level, change
    
    def _get_tasks_count_on_level(self, user_id: str, island_id: str, level: int) -> int:
        """Считает количество задач, решённых на данном уровне (упрощённо)"""
        # В полной версии: запрос к task_history
        # В MVP: возвращаем 3, чтобы не блокировать повышение
        return 3
    
    def _save_level(self, user_id: str, island_id: str, level: int):
        """Сохраняет уровень сложности для игрока"""
        user = self.storage.get_user(user_id)
        if not user:
            return
        
        key = f"difficulty_{island_id}"
        user[key] = level
        self.storage.save_user(user_id, user)
    
    def get_recommended_level(self, user_id: str, island_id: str, accuracy: float) -> int:
        """Рекомендует уровень на основе точности (для возврата в остров после Замка)"""
        if accuracy >= 0.90:
            return 5  # Матемаг
        elif accuracy >= 0.75:
            return 4  # Эксперт
        elif accuracy >= 0.60:
            return 3  # Вызов
        elif accuracy >= 0.40:
            return 2  # Нормально
        else:
            return 1  # Разминка