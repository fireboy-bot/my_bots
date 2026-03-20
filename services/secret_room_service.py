# services/secret_room_service.py
"""
Сервис Тайной комнаты — MVP версия.
Максимально просто, без лишних абстракций.
"""


class SecretRoomService:
    """Логика Тайной комнаты"""

    # Требования для входа
    MIN_LEVEL = 3
    MIN_TASKS_CORRECT = 10

    def can_enter(self, player: dict) -> bool:
        """
        Проверяет может ли игрок войти в Тайную комнату.
        """
        level = player.get("level", 1)
        tasks_correct = player.get("tasks_correct", 0)

        return level >= self.MIN_LEVEL or tasks_correct >= self.MIN_TASKS_CORRECT

    def get_stats(self, player: dict) -> dict:
        """
        Возвращает статистику игрока.
        """
        defeated_bosses = player.get("defeated_bosses", [])

        return {
            "level": player.get("level", 1),
            "total_score": player.get("total_score", 0),
            "bosses_defeated": len(defeated_bosses),
            "tasks_correct": player.get("tasks_correct", 0),
            "balance": player.get("score_balance", 0),
        }

    def get_message(self, player: dict) -> str:
        """
        Формирует сообщение для Зала Славы.
        """
        stats = self.get_stats(player)

        msg = "📊 <b>ЗАЛ СЛАВЫ</b>\n\n"
        msg += f"🎮 <b>Уровень:</b> {stats['level']}\n"
        msg += f"💰 <b>Всего очков:</b> {stats['total_score']:,}\n"
        msg += f"⚔️ <b>Боссов побеждено:</b> {stats['bosses_defeated']}\n"
        msg += f"🎯 <b>Задач решено:</b> {stats['tasks_correct']}\n"
        msg += f"💵 <b>Золотых:</b> {stats['balance']:,}\n"

        achievements = self._get_achievements(player)

        if achievements:
            msg += "\n🏆 <b>ТВОИ ТРОФЕИ:</b>\n"
            for achievement in achievements:
                msg += f"▫️ {achievement}\n"

        return msg

    def _get_achievements(self, player: dict) -> list:
        """
        Возвращает список достижений.
        """
        achievements = []

        defeated_bosses = player.get("defeated_bosses", [])
        level = player.get("level", 1)
        tasks_correct = player.get("tasks_correct", 0)

        if "final_boss" in defeated_bosses:
            achievements.append("🥇 Победитель Числяндии")

        if len(defeated_bosses) >= 3:
            achievements.append("⚔️ Укротитель Боссов")

        if level >= 10:
            achievements.append("🎯 Опытный Игрок")

        if level >= 20:
            achievements.append("🌟 Мастер Чисел")

        if tasks_correct >= 50:
            achievements.append("🧮 Решатель")

        if tasks_correct >= 100:
            achievements.append("📚 Учёный Числяндии")

        return achievements


__all__ = ["SecretRoomService"]