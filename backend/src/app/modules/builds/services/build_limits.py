"""Single source of truth for Build Designer quantity and row limits."""

from __future__ import annotations

UPGRADE_SLOT_LIMIT = 6
BASE_UPGRADE_SLOT_LIMIT = 4
CONSUMABLE_SLOT_LIMIT = 3
SPECIAL_CREW_TOTAL_LIMIT = 8
WEAPON_ARC_ROW_LIMIT = 12
DEDICATED_WEAPON_ROW_LIMIT = 8


def build_limits_for_api() -> dict[str, int]:
    """Expose only limits the browser must enforce interactively."""

    return {
        "special_crew_total": SPECIAL_CREW_TOTAL_LIMIT,
        "consumable_rows": CONSUMABLE_SLOT_LIMIT,
        "weapon_arc_rows": WEAPON_ARC_ROW_LIMIT,
        "dedicated_weapon_rows": DEDICATED_WEAPON_ROW_LIMIT,
        "upgrade_slots": UPGRADE_SLOT_LIMIT,
    }
