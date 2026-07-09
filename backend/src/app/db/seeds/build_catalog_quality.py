"""Catalog quality checks for Build Designer seed data."""

from __future__ import annotations

REQUIRED_SHIP_FIELDS = (
    "name",
    "rate",
    "ship_type",
    "durability",
    "speed_knots",
    "maneuverability",
    "armor",
    "hold_capacity",
    "crew_capacity",
    "sailor_minimum",
    "weapon_layout",
    "displacement_tons",
)

REQUIRED_UPGRADE_FIELDS = ("category", "name", "stat_effects")


def validate_ship_seed_data(rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("Ship seed catalog is empty.")
    names: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        if name.casefold() in names:
            errors.append(f"Duplicate ship name: {name}")
        names.add(name.casefold())
        for field in REQUIRED_SHIP_FIELDS:
            value = row.get(field)
            if value in (None, ""):
                errors.append(f"{name}: missing {field}")
        for field in ("durability", "hold_capacity", "crew_capacity", "displacement_tons"):
            if int(row.get(field) or 0) <= 0:
                errors.append(f"{name}: {field} must be positive")
        if int(row.get("durability") or 0) == 0 or int(row.get("hold_capacity") or 0) == 0:
            errors.append(f"{name}: catalog still contains zero-value prototype stats")
    if errors:
        raise RuntimeError("Ship seed catalog failed quality checks:\n" + "\n".join(f"- {error}" for error in errors))


def validate_upgrade_seed_data(rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("Upgrade seed catalog is empty.")
    names: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        if name.casefold() in names:
            errors.append(f"Duplicate upgrade name: {name}")
        names.add(name.casefold())
        for field in REQUIRED_UPGRADE_FIELDS:
            if row.get(field) in (None, ""):
                errors.append(f"{name}: missing {field}")
        effects = row.get("stat_effects")
        if not isinstance(effects, dict) or not effects:
            errors.append(f"{name}: stat_effects must be a non-empty object")
            continue
        for key, value in effects.items():
            if not isinstance(key, str) or not isinstance(value, (int, float)):
                errors.append(f"{name}: invalid effect {key!r}={value!r}")
    if errors:
        raise RuntimeError("Upgrade seed catalog failed quality checks:\n" + "\n".join(f"- {error}" for error in errors))
