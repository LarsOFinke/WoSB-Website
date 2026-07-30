"""Catalog quality checks for Build Designer master data."""

from __future__ import annotations

REQUIRED_UPGRADE_FIELDS = ("category", "name", "source", "notes", "option_kind", "stat_effects")
MIN_SAIL_OPTIONS = 9
MIN_LANTERN_OPTIONS = 9
MIN_UPGRADE_OPTIONS = 30
MIN_SPECIALIST_OPTIONS = 51


def validate_upgrade_seed_data(rows: list[dict[str, object]]) -> None:
    if len(rows) < MIN_UPGRADE_OPTIONS:
        raise RuntimeError(
            f"Upgrade seed catalog is incomplete: expected at least {MIN_UPGRADE_OPTIONS}, got {len(rows)}."
        )
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
        source = str(row.get("source") or "")
        if not source.startswith("WoSB in-game"):
            errors.append(f"{name}: source must identify the verified in-game upgrade panels")
        option_kind = str(row.get("option_kind") or "")
        if option_kind not in {
            "ship_upgrade_speed",
            "ship_upgrade_expeditionary",
            "ship_upgrade_protection",
            "ship_upgrade_combat",
            "ship_upgrade_unusual",
            "ship_upgrade_mortar",
        }:
            errors.append(f"{name}: invalid upgrade group {option_kind!r}")
        effects = row.get("stat_effects")
        if not isinstance(effects, dict) or not effects:
            errors.append(f"{name}: stat_effects must be a non-empty object")
            continue
        for key, value in effects.items():
            if not isinstance(key, str) or not isinstance(value, (int, float)):
                errors.append(f"{name}: invalid effect {key!r}={value!r}")
    if errors:
        raise RuntimeError(
            "Upgrade seed catalog failed quality checks:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


def _validate_numeric_effects(
    name: str, effects: object, errors: list[str], *, allow_empty: bool
) -> dict[str, int | float]:
    if not isinstance(effects, dict):
        errors.append(f"{name}: stat_effects must be an object")
        return {}
    if not allow_empty and not effects:
        errors.append(f"{name}: stat_effects must be a non-empty object")
        return {}
    for key, value in effects.items():
        if not isinstance(key, str) or not isinstance(value, (int, float)):
            errors.append(f"{name}: invalid effect {key!r}={value!r}")
    return effects


def validate_sail_seed_data(rows: list[dict[str, object]]) -> None:
    if len(rows) != MIN_SAIL_OPTIONS:
        raise RuntimeError(
            f"Sail seed catalog is incomplete: expected {MIN_SAIL_OPTIONS}, got {len(rows)}."
        )
    names: set[str] = set()
    seed_ids: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        seed_id = str(row.get("seed_id") or "").strip()
        if name.casefold() in names:
            errors.append(f"Duplicate sail name: {name}")
        names.add(name.casefold())
        if not seed_id:
            errors.append(f"{name}: stable seed_id is required")
        elif seed_id.casefold() in seed_ids:
            errors.append(f"Duplicate sail seed_id: {seed_id}")
        seed_ids.add(seed_id.casefold())
        if row.get("category") != "sail":
            errors.append(f"{name}: category must be sail")
        if row.get("option_kind") != "sail":
            errors.append(f"{name}: option_kind must be sail")
        if not str(row.get("source") or "").strip():
            errors.append(f"{name}: source is required")
        if not str(row.get("notes") or "").strip():
            errors.append(f"{name}: notes are required")
        effects = _validate_numeric_effects(
            name, row.get("stat_effects"), errors, allow_empty=False
        )
        if effects and not any(float(value) != 0 for value in effects.values()):
            errors.append(f"{name}: sail effects must change at least one calculator stat")
    if errors:
        raise RuntimeError(
            "Sail seed catalog failed quality checks:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


def validate_lantern_seed_data(rows: list[dict[str, object]]) -> None:
    if len(rows) != MIN_LANTERN_OPTIONS:
        raise RuntimeError(
            f"Lantern seed catalog is incomplete: expected {MIN_LANTERN_OPTIONS}, got {len(rows)}."
        )
    names: set[str] = set()
    seed_ids: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        seed_id = str(row.get("seed_id") or "").strip()
        if name.casefold() in names:
            errors.append(f"Duplicate lantern name: {name}")
        names.add(name.casefold())
        if not seed_id:
            errors.append(f"{name}: stable seed_id is required")
        elif seed_id.casefold() in seed_ids:
            errors.append(f"Duplicate lantern seed_id: {seed_id}")
        seed_ids.add(seed_id.casefold())
        if row.get("category") != "lantern":
            errors.append(f"{name}: category must be lantern")
        if row.get("option_kind") != "lantern":
            errors.append(f"{name}: option_kind must be lantern")
        if not str(row.get("source") or "").strip():
            errors.append(f"{name}: source is required")
        if not str(row.get("notes") or "").strip():
            errors.append(f"{name}: notes are required")
        effects = _validate_numeric_effects(
            name, row.get("stat_effects"), errors, allow_empty=False
        )
        if effects and not any(float(value) != 0 for value in effects.values()):
            errors.append(f"{name}: lantern effects must change at least one calculator stat")
    if errors:
        raise RuntimeError(
            "Lantern seed catalog failed quality checks:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


VALID_WEAPON_SLOT_TYPES = {
    "weapon_front",
    "weapon_rear",
    "weapon_port",
    "weapon_starboard",
    "weapon_mortar",
    "weapon_special",
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
        if option_kind not in {
            "cannon",
            "bow_stern",
            "mortar",
            "mortar_launcher",
            "special_weapon",
        }:
            errors.append(f"{name}: invalid weapon kind {option_kind!r}")
        allowed_raw = row.get("allowed_slot_types")
        if isinstance(allowed_raw, list):
            allowed = {str(slot).strip() for slot in allowed_raw if str(slot).strip()}
        else:
            allowed = {
                slot.strip() for slot in str(allowed_raw or "").split(",") if slot.strip()
            }
        if not allowed:
            errors.append(f"{name}: missing allowed_slot_types")
        unknown_slots = allowed - VALID_WEAPON_SLOT_TYPES
        if unknown_slots:
            errors.append(f"{name}: unknown slot type(s): {', '.join(sorted(unknown_slots))}")
        expected_slots = {
            "cannon": {"weapon_port", "weapon_starboard"},
            "bow_stern": {"weapon_front", "weapon_rear"},
            "mortar": {"weapon_mortar"},
            "mortar_launcher": {"weapon_mortar"},
            "special_weapon": {"weapon_front", "weapon_rear", "weapon_special"},
        }.get(option_kind)
        if expected_slots is not None and allowed != expected_slots:
            errors.append(
                f"{name}: {option_kind} weapons must use exactly "
                f"{', '.join(sorted(expected_slots))}"
            )
        weapon_class = row.get("weapon_class")
        if option_kind in {"cannon", "bow_stern"}:
            if weapon_class not in {"light", "medium", "heavy"}:
                family = "broadside cannons" if option_kind == "cannon" else "bow/stern weapons"
                errors.append(
                    f"{name}: {family} require light, medium or heavy weapon_class"
                )
        elif weapon_class not in (None, ""):
            errors.append(
                f"{name}: {option_kind} compatibility is defined by its dedicated mount rules "
                "and must not use weapon_class"
            )
        if option_kind == "mortar" and row.get("weapon_caliber_inches") in (None, ""):
            errors.append(f"{name}: mortar caliber is required")
        performance = row.get("weapon_performance")
        if performance is not None:
            if not isinstance(performance, dict):
                errors.append(f"{name}: weapon_performance must be an object")
            else:
                damage = performance.get("base_damage")
                reload_seconds = performance.get("reload_seconds")
                if not isinstance(damage, (int, float)) or damage < 0:
                    errors.append(f"{name}: weapon_performance.base_damage must be non-negative")
                if not isinstance(reload_seconds, (int, float)) or reload_seconds <= 0:
                    errors.append(f"{name}: weapon_performance.reload_seconds must be positive")
    if errors:
        raise RuntimeError(
            "Weapon seed catalog failed quality checks:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


def validate_special_crew_seed_data(rows: list[dict[str, object]]) -> None:
    if len(rows) != MIN_SPECIALIST_OPTIONS:
        raise RuntimeError(
            f"Specialist seed catalog is incomplete: expected {MIN_SPECIALIST_OPTIONS}, got {len(rows)}."
        )
    names: set[str] = set()
    seed_ids: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        name = str(row.get("name") or f"row #{index}")
        seed_id = str(row.get("seed_id") or "").strip()
        if name.casefold() in names:
            errors.append(f"Duplicate special crew name: {name}")
        names.add(name.casefold())
        if not seed_id:
            errors.append(f"{name}: stable seed_id is required")
        elif seed_id.casefold() in seed_ids:
            errors.append(f"Duplicate specialist seed_id: {seed_id}")
        seed_ids.add(seed_id.casefold())
        if row.get("category") != "special_crew":
            errors.append(f"{name}: category must be special_crew")
        if row.get("option_kind") != "crew_specialist":
            errors.append(f"{name}: option_kind must be crew_specialist")
        if not str(row.get("source") or "").strip():
            errors.append(f"{name}: source is required")
        notes = str(row.get("notes") or "").strip()
        if not notes:
            errors.append(f"{name}: notes are required")
        elif "Group:" not in notes:
            errors.append(f"{name}: notes must identify the Specialist group")
        _validate_numeric_effects(name, row.get("stat_effects"), errors, allow_empty=False)
    if errors:
        raise RuntimeError(
            "Special crew seed catalog failed quality checks:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


def validate_build_option_catalog(
    categories: list[dict[str, object]],
    option_groups: tuple[list[dict[str, object]], ...] | list[list[dict[str, object]]],
) -> None:
    """Validate the complete Build Designer catalog boundary.

    Detailed validators own category-specific rules. This cross-catalog guard
    makes sure every active category is represented, names are unique inside a
    category and every selectable row has traceable source metadata.
    """

    active_categories = {
        str(row.get("key") or "").strip() for row in categories if row.get("is_active", True)
    }
    rows = [row for group in option_groups for row in group]
    represented: set[str] = set()
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []

    for index, row in enumerate(rows, start=1):
        category = str(row.get("category") or "").strip()
        name = str(row.get("name") or "").strip()
        source = str(row.get("source") or "").strip()
        if not category:
            errors.append(f"row #{index}: missing category")
            continue
        represented.add(category)
        if category not in active_categories:
            errors.append(f"{name or f'row #{index}'}: unknown category {category!r}")
        if not name:
            errors.append(f"{category} row #{index}: missing name")
            continue
        pair = (category, name.casefold())
        if pair in seen:
            errors.append(f"Duplicate option in {category}: {name}")
        seen.add(pair)
        if not source:
            errors.append(f"{category}/{name}: source is required")

    missing = active_categories - represented
    if missing:
        errors.append(f"Categories without options: {', '.join(sorted(missing))}")

    if errors:
        raise RuntimeError(
            "Build option catalog failed quality checks:\n"
            + "\n".join(f"- {error}" for error in errors)
        )
