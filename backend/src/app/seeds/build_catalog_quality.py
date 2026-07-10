"""Catalog quality checks for Build Designer seed data."""

from __future__ import annotations

import re

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
        layout = str(row.get("weapon_layout") or "").strip()
        if not re.fullmatch(r"\d+\s*-\s*\d+\s*-\s*\d+(?:\s*\+\s*mortar\s+\d+(?:\.\d+)?in\s+x\d+)?", layout, re.IGNORECASE):
            errors.append(f"{name}: invalid weapon_layout format {layout!r}")
        if not str(row.get("source") or "").startswith("WoSB wiki"):
            errors.append(f"{name}: source must identify the audited WoSB wiki catalog")
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


VALID_WEAPON_SLOT_TYPES = {
    "weapon_front",
    "weapon_rear",
    "weapon_port",
    "weapon_starboard",
    "weapon_mortar",
}


def validate_weapon_seed_data(rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("Weapon seed catalog is empty.")
    names: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        if name.casefold() in names:
            errors.append(f"Duplicate weapon name: {name}")
        names.add(name.casefold())
        if row.get("category") != "weapon":
            errors.append(f"{name}: category must be weapon")
        option_kind = row.get("option_kind")
        if option_kind not in {"cannon", "bow_stern", "mortar"}:
            errors.append(f"{name}: invalid weapon kind {option_kind!r}")
        allowed_raw = row.get("allowed_slot_types")
        allowed = {slot.strip() for slot in str(allowed_raw or "").split(",") if slot.strip()}
        if not allowed:
            errors.append(f"{name}: missing allowed_slot_types")
        unknown_slots = allowed - VALID_WEAPON_SLOT_TYPES
        if unknown_slots:
            errors.append(f"{name}: unknown slot type(s): {', '.join(sorted(unknown_slots))}")
        expected_slots = {
            "cannon": {"weapon_port", "weapon_starboard"},
            "bow_stern": {"weapon_front", "weapon_rear"},
            "mortar": {"weapon_mortar"},
        }.get(option_kind)
        if expected_slots is not None and allowed != expected_slots:
            errors.append(
                f"{name}: {option_kind} weapons must use exactly "
                f"{', '.join(sorted(expected_slots))}"
            )
    if errors:
        raise RuntimeError("Weapon seed catalog failed quality checks:\n" + "\n".join(f"- {error}" for error in errors))


def validate_special_crew_seed_data(rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("Special crew seed catalog is empty.")
    names: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        if name.casefold() in names:
            errors.append(f"Duplicate special crew name: {name}")
        names.add(name.casefold())
        if row.get("category") != "special_crew":
            errors.append(f"{name}: category must be special_crew")
        effects = row.get("stat_effects")
        if not isinstance(effects, dict) or not effects:
            errors.append(f"{name}: stat_effects must be a non-empty object")
    if errors:
        raise RuntimeError("Special crew seed catalog failed quality checks:\n" + "\n".join(f"- {error}" for error in errors))
