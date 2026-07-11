"""Verified lantern catalog used by the Build Designer.

Values are transcribed from the in-game tooltip screenshots supplied by the
project owner. Percentage effects are stored as normalized modifiers and are
used identically by the live frontend preview and the backend calculation.

All records remain editable through the master-data admin. Deliberate admin
overrides are protected from later seed runs.
"""

LANTERN_CATALOG_REVISION = "tooltip-lantern-catalog-2026-07-v3"


def _lantern(
    seed_id: str,
    name: str,
    notes: str,
    stat_effects: dict[str, int | float],
) -> dict[str, object]:
    return {
        "category": "lantern",
        "seed_id": seed_id,
        "name": name,
        "source": LANTERN_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "lantern",
        "stat_effects": stat_effects,
    }


LANTERN_OPTIONS = [
    _lantern(
        "blue",
        "Blue Lantern",
        "Verified in-game tooltip: +6% speed.",
        {"speed_pct": 6},
    ),
    _lantern(
        "bright",
        "Bright Lantern",
        "Verified in-game tooltip: +12% cargo hold.",
        {"hold_capacity_pct": 12},
    ),
    _lantern(
        "golden",
        "Golden Lantern",
        "Verified in-game tooltip: +5% speed, armor and damage.",
        {"speed_pct": 5, "armor_pct": 5, "damage_pct": 5},
    ),
    _lantern(
        "green",
        "Green Lantern",
        "Verified in-game tooltip: +7% durability.",
        {"hull_hp_pct": 7},
    ),
    _lantern(
        "lilac",
        "Lilac Lantern",
        "Verified in-game tooltip: +7% maneuverability.",
        {"turn_rate_pct": 7},
    ),
    _lantern(
        "red",
        "Red Lantern",
        "Verified in-game tooltip: +5% maneuverability, +5% damage and +7% experience/loot.",
        {"turn_rate_pct": 5, "damage_pct": 5, "exp_loot_pct": 7},
    ),
    _lantern(
        "white",
        "White Lantern",
        "Verified in-game tooltip: +10% experience/loot.",
        {"exp_loot_pct": 10},
    ),
    _lantern(
        "yellow",
        "Yellow Lantern",
        "Verified in-game tooltip: +7% damage.",
        {"damage_pct": 7},
    ),
]

LANTERN_EFFECTS_BY_SEED_ID: dict[str, dict[str, int | float]] = {
    str(row["seed_id"]): dict(row["stat_effects"])
    for row in LANTERN_OPTIONS
}
