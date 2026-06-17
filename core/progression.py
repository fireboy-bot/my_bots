"""
Прогрессия миров — единый каталог для Telegram и Web.
Метаданные островов синхронизированы с handlers/levels.py (island_themes).
"""

from typing import Any, Dict, List, Optional

WORLD_CATALOG: List[Dict[str, str]] = [
    {
        "id": "addition",
        "emoji": "🌅",
        "name": "Остров Сложения",
        "short_name": "Сложение",
        "tier": "island",
    },
    {
        "id": "subtraction",
        "emoji": "🌑",
        "name": "Пещера Вычитания",
        "short_name": "Вычитание",
        "tier": "island",
    },
    {
        "id": "multiplication",
        "emoji": "🌳",
        "name": "Лес Умножения",
        "short_name": "Умножение",
        "tier": "island",
    },
    {
        "id": "division",
        "emoji": "🌊",
        "name": "Река Деления",
        "short_name": "Деление",
        "tier": "island",
    },
    {
        "id": "time_world",
        "emoji": "🕒",
        "name": "Мир Времени",
        "short_name": "Время",
        "tier": "world",
    },
    {
        "id": "measure_world",
        "emoji": "📏",
        "name": "Мир Мер",
        "short_name": "Меры",
        "tier": "world",
    },
    {
        "id": "logic_world",
        "emoji": "🧠",
        "name": "Мир Логики",
        "short_name": "Логика",
        "tier": "world",
    },
]

ZONE_NAMES_RU = {w["id"]: w["short_name"] for w in WORLD_CATALOG}

# Цепочка открытия после прохождения острова (handlers/levels.py)
ISLAND_UNLOCK_CHAIN = {
    "addition": "subtraction",
    "subtraction": "multiplication",
    "multiplication": "division",
}

DEFAULT_UNLOCKED = ["addition"]


def get_unlocked_zones(user: Optional[Dict[str, Any]]) -> List[str]:
    if not user:
        return list(DEFAULT_UNLOCKED)
    zones = user.get("unlocked_zones")
    if not zones or not isinstance(zones, list):
        return list(DEFAULT_UNLOCKED)
    return list(zones)


def is_world_unlocked(user: Optional[Dict[str, Any]], world_id: str) -> bool:
    return world_id in set(get_unlocked_zones(user))


def get_world_meta(world_id: str) -> Optional[Dict[str, str]]:
    for world in WORLD_CATALOG:
        if world["id"] == world_id:
            return dict(world)
    return None


def list_worlds_for_user(user: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Список миров с флагом unlocked — для экрана выбора в Web."""
    unlocked = set(get_unlocked_zones(user))
    worlds: List[Dict[str, Any]] = []
    for meta in WORLD_CATALOG:
        worlds.append(
            {
                **meta,
                "unlocked": meta["id"] in unlocked,
            }
        )
    return worlds


def resolve_playable_world(user: Optional[Dict[str, Any]], world_id: Optional[str]) -> Optional[str]:
    """Проверяет, что мир существует и открыт игроку."""
    if not world_id:
        zones = get_unlocked_zones(user)
        return zones[-1] if zones else "addition"
    if not get_world_meta(world_id):
        return None
    if not is_world_unlocked(user, world_id):
        return None
    return world_id
