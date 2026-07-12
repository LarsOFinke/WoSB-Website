from __future__ import annotations

import re

WEAPON_CLASS_DATA = (
    {"code": "light", "label": "Light", "rank": 10},
    {"code": "medium", "label": "Medium", "rank": 20},
    {"code": "heavy", "label": "Heavy", "rank": 30},
)

WEAPON_SLOT_TYPE_DATA = (
    {"code": "weapon_front", "label": "Bow weapons", "sort_order": 10},
    {"code": "weapon_rear", "label": "Stern weapons", "sort_order": 20},
    {"code": "weapon_port", "label": "Port broadside", "sort_order": 30},
    {"code": "weapon_starboard", "label": "Starboard broadside", "sort_order": 40},
    {"code": "weapon_mortar", "label": "Mortars", "sort_order": 50},
    {"code": "weapon_special", "label": "Special weapons", "sort_order": 60},
)

# The Build Designer uses the game's Light/Medium/Heavy weapon taxonomy.
# Ship rate is the stable catalog attribute available for every seeded ship;
# exceptional ships can override the class explicitly in their seed later.
MAX_WEAPON_CLASS_BY_RATE = {
    1: "heavy",
    2: "heavy",
    3: "heavy",
    4: "medium",
    5: "medium",
    6: "light",
    7: "light",
}


def parse_weapon_layout(
    layout: str | None,
    *,
    rate: int,
    max_weapon_class: str | None = None,
    special_weapon_capacity: int = 0,
) -> list[dict[str, object]]:
    text = (layout or "").strip().lower().replace(";", " + ")
    regular_match = re.search(r"(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", text)
    front, broadside, rear = (0, 0, 0)
    if regular_match:
        front, broadside, rear = (int(regular_match.group(index)) for index in (1, 2, 3))

    weapon_class = max_weapon_class or (
        MAX_WEAPON_CLASS_BY_RATE[int(rate)] if any((front, broadside, rear)) else None
    )
    rows: list[dict[str, object]] = [
        {"slot_type": "weapon_front", "capacity": front, "max_weapon_class": weapon_class},
        {"slot_type": "weapon_rear", "capacity": rear, "max_weapon_class": weapon_class},
        {"slot_type": "weapon_port", "capacity": broadside, "max_weapon_class": weapon_class},
        {"slot_type": "weapon_starboard", "capacity": broadside, "max_weapon_class": weapon_class},
    ]
    mortar_match = re.search(r"mortar\s+(\d+(?:\.\d+)?)\s*in\s*x\s*(\d+)", text)
    if mortar_match:
        rows.append(
            {
                "slot_type": "weapon_mortar",
                "capacity": int(mortar_match.group(2)),
                "max_weapon_class": None,
                "max_caliber_inches": float(mortar_match.group(1)),
            }
        )
    else:
        rows.append(
            {
                "slot_type": "weapon_mortar",
                "capacity": 0,
                "max_weapon_class": None,
                "max_caliber_inches": None,
            }
        )
    rows.append(
        {
            "slot_type": "weapon_special",
            "capacity": max(0, int(special_weapon_capacity or 0)),
            "max_weapon_class": None,
            "max_caliber_inches": None,
        }
    )
    return rows
