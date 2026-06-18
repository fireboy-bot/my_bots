"""
Инвентарь игрока для Web API.
"""

from collections import Counter
from typing import Any, Dict, List


from core.item_display import get_item_display


def _item_label(item_id: str) -> str:
    return get_item_display(item_id)


def build_inventory_view(user: Dict[str, Any]) -> Dict[str, Any]:
    inventory = list(user.get("inventory") or [])
    rewards = list(user.get("rewards") or [])
    artifact_upgrades = user.get("artifact_upgrades") or {}

    consumables: List[Dict[str, Any]] = []
    for item_id, count in sorted(Counter(inventory).items()):
        consumables.append(
            {
                "id": item_id,
                "label": _item_label(item_id),
                "count": count,
                "category": "consumable",
            }
        )

    trophies: List[Dict[str, Any]] = []
    for reward_id in rewards:
        trophies.append(
            {
                "id": reward_id,
                "label": _item_label(reward_id),
                "category": "trophy",
            }
        )

    artifacts: List[Dict[str, Any]] = []
    for art_id, level in sorted(artifact_upgrades.items()):
        lvl = level.get("level", level) if isinstance(level, dict) else int(level or 0)
        if lvl > 0:
            artifacts.append(
                {
                    "id": art_id,
                    "label": _item_label(art_id),
                    "level": lvl,
                    "category": "artifact",
                }
            )

    secret_items = []
    profile = user.get("player_profile") or {}
    room_items = (profile.get("secret_room") or {}).get("room_items") or user.get("secret_room_items") or []
    for item_id in room_items:
        secret_items.append(
            {
                "id": item_id,
                "label": item_id.replace("_", " ").title(),
                "category": "secret",
            }
        )

    total = len(inventory) + len(trophies) + len(artifacts) + len(secret_items)

    return {
        "consumables": consumables,
        "trophies": trophies,
        "artifacts": artifacts,
        "secret_items": secret_items,
        "total_count": total,
        "is_empty": total == 0,
    }
