"""Lantern catalog used by the Build Designer.

Functional lantern families expose normalized stat effects. Cosmetic/event
families remain selectable without inventing combat modifiers. Every value can
be reviewed and overridden in the master-data admin.
"""

LANTERN_CATALOG_REVISION = "B20-build-designer-lanterns-2026-07"


def _lantern(
    seed_id: str,
    name: str,
    notes: str,
    stat_effects: dict[str, int | float] | None = None,
) -> dict[str, object]:
    return {
        "category": "lantern",
        "seed_id": seed_id,
        "name": name,
        "source": LANTERN_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "lantern",
        "stat_effects": stat_effects or {},
    }


LANTERN_OPTIONS = [
    _lantern("black", "Black Lantern", "Dark cosmetic lantern family."),
    _lantern("blue", "Blue Lantern", "Blue cosmetic lantern family."),
    _lantern("festival", "Festival Lantern", "Seasonal festival lantern family."),
    _lantern("golden", "Golden Lantern", "Adds 1,000 units of cargo hold capacity.", {"hold_capacity": 1000}),
    _lantern("green", "Green Lantern", "Green cosmetic lantern family."),
    _lantern("ice", "Ice Lantern", "Increases broadside armor by 2%.", {"armor_pct": 2}),
    _lantern("imperial", "Imperial Lantern", "Imperial cosmetic reward lantern family."),
    _lantern("jack-o-lantern", "Jack-o'-Lantern", "Halloween event lantern family."),
    _lantern("pirate", "Pirate Lantern", "Pirate-themed cosmetic lantern family."),
    _lantern("red", "Red Lantern", "Increases reload speed by 3%.", {"reload_pct": 3}),
    _lantern("storm", "Storm Lantern", "Increases ship speed by 3%.", {"speed_pct": 3}),
    _lantern("white", "White Lantern", "White cosmetic lantern family."),
]
