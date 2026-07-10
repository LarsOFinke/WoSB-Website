"""Lantern catalog used by the Build Designer.

Lantern bonuses are deliberately not simulated until a stable machine-readable
export exists. The catalog is nevertheless complete for fleet presets: every
known visual/event family can be selected and older local rows are deactivated
by the idempotent seed manager when they disappear from this list.
"""

LANTERN_CATALOG_REVISION = "B20-fleet-audit-2026-07"


def _lantern(name: str, notes: str) -> dict[str, object]:
    return {
        "category": "lantern",
        "name": name,
        "source": LANTERN_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "lantern",
    }


LANTERN_OPTIONS = [
    _lantern("Black Lantern", "Dark cosmetic lantern family; bonus is intentionally not simulated."),
    _lantern("Blue Lantern", "Blue cosmetic lantern family; bonus is intentionally not simulated."),
    _lantern("Festival Lantern", "Seasonal festival lantern family; bonus is intentionally not simulated."),
    _lantern("Golden Lantern", "Golden lantern family retained for existing presets."),
    _lantern("Green Lantern", "Green cosmetic lantern family; bonus is intentionally not simulated."),
    _lantern("Ice Lantern", "Winter event lantern family retained for existing presets."),
    _lantern("Imperial Lantern", "Imperial reward lantern family; bonus is intentionally not simulated."),
    _lantern("Jack-o'-Lantern", "Halloween event lantern family; bonus is intentionally not simulated."),
    _lantern("Pirate Lantern", "Pirate-themed lantern family; bonus is intentionally not simulated."),
    _lantern("Red Lantern", "Red lantern family retained for existing presets."),
    _lantern("Storm Lantern", "Storm event lantern family retained for existing presets."),
    _lantern("White Lantern", "White cosmetic lantern family; bonus is intentionally not simulated."),
]
