"""Single source of truth for Build Designer quantity and row limits."""

from __future__ import annotations

UPGRADE_SLOT_LIMIT = 8
BASE_UPGRADE_SLOT_LIMIT = 4
CONSUMABLE_SLOT_LIMIT = 3
SPECIAL_CREW_SLOT_LIMIT = 8
# Backward-compatible alias for older API consumers.
SPECIAL_CREW_TOTAL_LIMIT = SPECIAL_CREW_SLOT_LIMIT
WEAPON_ARC_ROW_LIMIT = 12
DEDICATED_WEAPON_ROW_LIMIT = 8


def build_limits_for_api() -> dict[str, int]:
    """Expose only limits the browser must enforce interactively."""

    return {
        "special_crew_rows": SPECIAL_CREW_SLOT_LIMIT,
        "special_crew_total": SPECIAL_CREW_SLOT_LIMIT,
        "consumable_rows": CONSUMABLE_SLOT_LIMIT,
        "weapon_arc_rows": WEAPON_ARC_ROW_LIMIT,
        "dedicated_weapon_rows": DEDICATED_WEAPON_ROW_LIMIT,
        "upgrade_slots": UPGRADE_SLOT_LIMIT,
    }
