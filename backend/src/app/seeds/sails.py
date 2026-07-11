"""Sail catalog for the Build Designer.

Only values verified from an in-game tooltip are applied as calculation data.
Unknown values deliberately remain empty instead of presenting invented
percentages. Admin overrides can fill reviewed values without being overwritten
by later seed runs.
"""

SAIL_CATALOG_REVISION = "B20-sail-tooltip-audit-2026-07"


def _sail(
    seed_id: str,
    name: str,
    notes: str,
    stat_effects: dict[str, int | float] | None = None,
) -> dict[str, object]:
    return {
        "category": "sail",
        "seed_id": seed_id,
        "name": name,
        "source": SAIL_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "sail",
        "stat_effects": stat_effects or {},
    }


SAIL_OPTIONS = [
    _sail(
        "tarpaulin",
        "Tarpaulin Sails",
        "Catalog entry retained; exact current tooltip modifiers are not yet verified and are intentionally not calculated.",
    ),
    _sail(
        "raiding",
        "Raiding Sails",
        "Verified tooltip: +4.1 kn ship speed and -20% cruising-speed gain.",
        {"speed_knots": 4.1, "cruising_speed_gain_pct": -20},
    ),
    _sail(
        "imported",
        "Imported Sails",
        "Catalog entry retained; exact current tooltip modifiers are not yet verified and are intentionally not calculated.",
    ),
    _sail(
        "elite",
        "Elite Sails",
        "Catalog entry retained; exact current tooltip modifiers are not yet verified and are intentionally not calculated.",
    ),
]
