"""Lantern catalog used by the Build Designer.

The previous numeric effects were planning assumptions, not audited game
values. They are removed rather than silently feeding incorrect values into the
live calculator. The records remain fully editable through master data admin,
so reviewed tooltip values can be added without a schema change.
"""

LANTERN_CATALOG_REVISION = "B20-lantern-tooltip-audit-2026-07"


def _lantern(seed_id: str, name: str, notes: str) -> dict[str, object]:
    return {
        "category": "lantern",
        "seed_id": seed_id,
        "name": name,
        "source": LANTERN_CATALOG_REVISION,
        "notes": notes,
        "option_kind": "lantern",
        "stat_effects": {},
    }


_UNVERIFIED = (
    "Selectable lantern catalog entry. The old planning modifier was removed; "
    "add the exact current tooltip values in Admin → Master data after verification."
)

LANTERN_OPTIONS = [
    _lantern("black", "Black Lantern", _UNVERIFIED),
    _lantern("blue", "Blue Lantern", _UNVERIFIED),
    _lantern("festival", "Festival Lantern", _UNVERIFIED),
    _lantern("golden", "Golden Lantern", _UNVERIFIED),
    _lantern("green", "Green Lantern", _UNVERIFIED),
    _lantern("ice", "Ice Lantern", _UNVERIFIED),
    _lantern("imperial", "Imperial Lantern", _UNVERIFIED),
    _lantern("jack-o-lantern", "Jack-o'-Lantern", _UNVERIFIED),
    _lantern("pirate", "Pirate Lantern", _UNVERIFIED),
    _lantern("red", "Red Lantern", _UNVERIFIED),
    _lantern("storm", "Storm Lantern", _UNVERIFIED),
    _lantern("white", "White Lantern", _UNVERIFIED),
]
