"""Sail options and their Build Designer speed modifiers.

The values are isolated seed defaults and remain editable through the master
-data admin. Stable seed ids allow labels to change later without creating
new records.
"""

SAIL_CATALOG_REVISION = "B20-build-designer-sails-2026-07"


def _sail(seed_id: str, name: str, speed_pct: int, notes: str) -> dict[str, object]:
    return {
        "category": "sail",
        "seed_id": seed_id,
        "name": name,
        "source": SAIL_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "sail",
        "stat_effects": {"speed_pct": speed_pct},
    }


SAIL_OPTIONS = [
    _sail("tarpaulin", "Tarpaulin Sails", 2, "Entry sail set; increases ship speed by 2%."),
    _sail("raiding", "Raiding Sails", 4, "Raiding sail set; increases ship speed by 4%."),
    _sail("imported", "Imported Sails", 6, "Imported sail set; increases ship speed by 6%."),
    _sail("elite", "Elite Sails", 8, "Elite sail set; increases ship speed by 8%."),
]
