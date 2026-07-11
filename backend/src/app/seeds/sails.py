"""Verified sail catalog for the Build Designer.

Values are transcribed from the in-game tooltip screenshots supplied by the
project owner. The leading value on every sail is treated as an absolute speed
bonus in knots. Conditional cruising modifiers remain separate effects so the
Build Designer can display them without incorrectly applying them to the base
ship speed at all times.

All records remain editable through the master-data admin. Deliberate admin
overrides are protected from later seed runs.
"""

SAIL_CATALOG_REVISION = "tooltip-sail-catalog-2026-07-v3"


def _sail(
    seed_id: str,
    name: str,
    notes: str,
    stat_effects: dict[str, int | float],
) -> dict[str, object]:
    return {
        "category": "sail",
        "seed_id": seed_id,
        "name": name,
        "source": SAIL_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "sail",
        "stat_effects": stat_effects,
    }


SAIL_OPTIONS = [
    _sail(
        "cheap",
        "Cheap Sails",
        "Verified in-game tooltip: +2 kn speed.",
        {"speed_knots": 2},
    ),
    _sail(
        "stitched",
        "Stitched Sails",
        "Verified in-game tooltip: +2.4 kn speed.",
        {"speed_knots": 2.4},
    ),
    _sail(
        "ultra-light",
        "Ultra-light Sails",
        "Verified in-game tooltip: +2.4 kn speed, +15% maneuverability in cruising mode and -30% speed while turning in cruising mode.",
        {
            "speed_knots": 2.4,
            "cruising_maneuverability_pct": 15,
            "cruising_turn_speed_penalty_pct": -30,
        },
    ),
    _sail(
        "storm",
        "Storm Sails",
        "Verified in-game tooltip: +2.7 kn speed and +2.5 kn cruising-speed bonus in strong wind.",
        {
            "speed_knots": 2.7,
            "strong_wind_cruising_speed_bonus_knots": 2.5,
        },
    ),
    _sail(
        "elite",
        "Elite Sails",
        "Verified in-game tooltip: +2.8 kn speed.",
        {"speed_knots": 2.8},
    ),
    _sail(
        "tacking",
        "Tacking Sails",
        "Verified in-game tooltip: +2.8 kn speed, turning grants +2 kn cruising-speed bonus and cruising-mode maneuverability is reduced by 20%.",
        {
            "speed_knots": 2.8,
            "turning_cruising_speed_bonus_knots": 2,
            "cruising_maneuverability_pct": -20,
        },
    ),
    _sail(
        "reefed",
        "Reefed Sails",
        "Verified in-game tooltip: +2.9 kn speed, -100% running-before-the-wind speed bonus and -50% broad-reach cruising-speed bonus.",
        {
            "speed_knots": 2.9,
            "running_before_wind_speed_penalty_pct": -100,
            "broad_reach_cruising_speed_bonus_pct": -50,
        },
    ),
    _sail(
        "tarpaulin",
        "Tarpaulin Sails",
        "Verified in-game tooltip: +3.1 kn speed and -2 maneuverability.",
        {"speed_knots": 3.1, "maneuverability": -2},
    ),
    _sail(
        "raiding",
        "Raiding Sails",
        "Verified in-game tooltip: +4.1 kn speed, -20% maneuverability in cruising mode and -20% cruising-speed gain.",
        {
            "speed_knots": 4.1,
            "cruising_maneuverability_pct": -20,
            "cruising_speed_gain_pct": -20,
        },
    ),
]

SAIL_EFFECTS_BY_SEED_ID: dict[str, dict[str, int | float]] = {
    str(row["seed_id"]): dict(row["stat_effects"])
    for row in SAIL_OPTIONS
}
