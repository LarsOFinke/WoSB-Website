from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.build_item_option_slot import BuildItemOptionSlotType
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.ships.models.weapon_mount import WeaponClassDefinition, WeaponSlotType
from app.seeds.ammunition import AMMUNITION_OPTIONS
from app.seeds.build_catalog_quality import (
    validate_build_option_catalog,
    validate_lantern_seed_data,
    validate_sail_seed_data,
    validate_special_crew_seed_data,
    validate_upgrade_seed_data,
    validate_weapon_seed_data,
)
from app.seeds.catalog_sync import mark_seed_applied, seed_key, should_apply_seed
from app.seeds.categories import BUILD_ITEM_CATEGORIES
from app.seeds.consumables import CONSUMABLE_OPTIONS
from app.seeds.hold_items import HOLD_OPTIONS
from app.seeds.lanterns import LANTERN_OPTIONS
from app.seeds.sails import SAIL_OPTIONS
from app.seeds.special_crew import SPECIAL_CREW_OPTIONS
from app.seeds.upgrades import LEGACY_UPGRADE_NAME_ALIASES, UPGRADE_OPTIONS
from app.seeds.weapons import WEAPON_OPTIONS

BUILD_OPTION_SEED_GROUPS = (
    SAIL_OPTIONS,
    UPGRADE_OPTIONS,
    LANTERN_OPTIONS,
    AMMUNITION_OPTIONS,
    CONSUMABLE_OPTIONS,
    HOLD_OPTIONS,
    WEAPON_OPTIONS,
    SPECIAL_CREW_OPTIONS,
)


def seed_build_option_catalog(db: Session) -> None:
    _validate_catalog()
    categories = _seed_categories(db)
    _migrate_legacy_upgrade_names(db, categories["upgrade"])
    _seed_options(db, categories)
    db.commit()


def _validate_catalog() -> None:
    validate_build_option_catalog(BUILD_ITEM_CATEGORIES, BUILD_OPTION_SEED_GROUPS)
    validate_sail_seed_data(SAIL_OPTIONS)
    validate_upgrade_seed_data(UPGRADE_OPTIONS)
    validate_lantern_seed_data(LANTERN_OPTIONS)
    validate_weapon_seed_data(WEAPON_OPTIONS)
    validate_special_crew_seed_data(SPECIAL_CREW_OPTIONS)


def _seed_categories(db: Session) -> dict[str, BuildItemCategory]:
    categories: dict[str, BuildItemCategory] = {}
    active_seed_keys: set[str] = set()

    for category_data in BUILD_ITEM_CATEGORIES:
        key = seed_key("build-category", category_data["key"])
        active_seed_keys.add(key)
        existing = db.scalar(select(BuildItemCategory).where(BuildItemCategory.seed_key == key))
        if existing is None:
            candidate = db.scalar(
                select(BuildItemCategory).where(BuildItemCategory.key == category_data["key"])
            )
            if candidate is not None and candidate.seed_revision == "custom":
                raise ValueError(
                    f"Custom category {candidate.key!r} conflicts with seed key {key!r}."
                )
            existing = candidate

        payload = {**category_data, "is_active": category_data.get("is_active", True)}
        if existing is None:
            existing = BuildItemCategory(**payload)
            db.add(existing)
            db.flush()
        elif existing.seed_key is None:
            existing.seed_key = key

        if should_apply_seed(existing, payload=payload):
            for field_name, value in payload.items():
                setattr(existing, field_name, value)
            mark_seed_applied(existing, key=key, payload=payload)
        categories[str(category_data["key"])] = existing

    for category in db.scalars(
        select(BuildItemCategory).where(BuildItemCategory.seed_key.is_not(None))
    ).all():
        if category.seed_key not in active_seed_keys and not category.is_seed_overridden:
            category.is_active = False
            category.seed_revision = None
            category.seed_checksum = None
    return categories


def _seed_options(db: Session, categories: dict[str, BuildItemCategory]) -> None:
    weapon_classes = {
        row.code: row for row in db.scalars(select(WeaponClassDefinition)).all()
    }
    slot_types = {row.code: row for row in db.scalars(select(WeaponSlotType)).all()}
    active_seed_keys: set[str] = set()

    for option_group in BUILD_OPTION_SEED_GROUPS:
        rows = sorted(option_group, key=lambda row: str(row["name"]).casefold())
        for sort_order, option_data in enumerate(rows, start=10):
            category_key = str(option_data["category"])
            category = categories[category_key]
            option_name = str(option_data["name"]).strip()
            stable_id = option_data.get("seed_id", option_name)
            key = seed_key("build-option", category_key, stable_id)
            active_seed_keys.add(key)

            existing = db.scalar(select(BuildItemOption).where(BuildItemOption.seed_key == key))
            if existing is None:
                candidate = db.scalar(
                    select(BuildItemOption).where(
                        BuildItemOption.category_id == category.id,
                        BuildItemOption.name == option_name,
                    )
                )
                if candidate is not None and candidate.seed_revision == "custom":
                    raise ValueError(
                        f"Custom option {category_key}/{candidate.name!r} conflicts with "
                        f"seed key {key!r}. Rename it or assign a different seed_id."
                    )
                existing = candidate

            effects = _numeric_effects(option_data.get("stat_effects"))
            allowed_codes = _slot_codes(option_data.get("allowed_slot_types"))
            payload = {
                "category_id": category.id,
                "name": option_name,
                "source": option_data.get("source"),
                "notes": option_data.get("notes"),
                "image_url": option_data.get("image_url"),
                "option_kind": option_data.get("option_kind"),
                "weapon_class_id": (
                    weapon_classes[str(option_data["weapon_class"])].id
                    if option_data.get("weapon_class")
                    else None
                ),
                "weapon_caliber_inches": option_data.get("weapon_caliber_inches"),
                "sort_order": sort_order * 10,
                "is_active": option_data.get("is_active", True),
            }
            canonical_payload = {
                "category": category_key,
                "name": option_name,
                "source": option_data.get("source"),
                "notes": option_data.get("notes"),
                "image_url": option_data.get("image_url"),
                "option_kind": option_data.get("option_kind"),
                "weapon_class": option_data.get("weapon_class"),
                "weapon_caliber_inches": option_data.get("weapon_caliber_inches"),
                "sort_order": sort_order * 10,
                "is_active": option_data.get("is_active", True),
                "stat_effects": effects,
                "allowed_slot_types": sorted(allowed_codes),
            }

            if existing is None:
                existing = BuildItemOption(**payload)
                db.add(existing)
                db.flush()
            elif existing.seed_key is None:
                existing.seed_key = key
            if not should_apply_seed(existing, payload=canonical_payload):
                continue

            for field_name, value in payload.items():
                setattr(existing, field_name, value)
            _sync_effects(existing, effects)
            _sync_slot_types(existing, allowed_codes, slot_types)
            mark_seed_applied(existing, key=key, payload=canonical_payload)

    for option in db.scalars(
        select(BuildItemOption).where(BuildItemOption.seed_key.is_not(None))
    ).all():
        if option.seed_key not in active_seed_keys and not option.is_seed_overridden:
            option.is_active = False
            option.seed_revision = None
            option.seed_checksum = None


def _numeric_effects(raw: object) -> dict[str, int | float]:
    if not isinstance(raw, dict):
        return {}
    return {
        key: value
        for key, value in raw.items()
        if isinstance(key, str) and isinstance(value, (int, float))
    }


def _slot_codes(raw: object) -> set[str]:
    return {code.strip() for code in str(raw or "").split(",") if code.strip()}


def _sync_slot_types(
    option: BuildItemOption,
    codes: set[str],
    slot_types: dict[str, WeaponSlotType],
) -> None:
    unknown = codes.difference(slot_types)
    if unknown:
        raise ValueError(f"Unknown weapon slot types for {option.name}: {sorted(unknown)}")
    current = {link.slot_type.code: link for link in option.slot_type_links}
    for code in codes:
        if code not in current:
            option.slot_type_links.append(
                BuildItemOptionSlotType(slot_type_id=slot_types[code].id)
            )
    for code, link in list(current.items()):
        if code not in codes:
            option.slot_type_links.remove(link)


def _sync_effects(option: BuildItemOption, effects: dict[str, int | float]) -> None:
    current = {effect.effect_key: effect for effect in option.effects}
    for key, value in sorted(effects.items()):
        if key in current:
            current[key].effect_value = float(value)
        else:
            option.effects.append(BuildItemEffect(effect_key=key, effect_value=float(value)))
    for key, effect in list(current.items()):
        if key not in effects:
            option.effects.remove(effect)


def _migrate_legacy_upgrade_names(db: Session, category: BuildItemCategory) -> None:
    """Preserve saved builds while moving renamed upgrade options forward."""

    for legacy_name, current_name in LEGACY_UPGRADE_NAME_ALIASES.items():
        legacy = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == legacy_name,
            )
        )
        if legacy is None or legacy.is_seed_overridden:
            continue

        current = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == current_name,
            )
        )
        if current is None:
            legacy.name = current_name
            legacy.is_active = True
            db.flush()
            continue

        db.execute(update(BuildSlot).where(BuildSlot.option_id == legacy.id).values(option_id=current.id))
        db.delete(legacy)
        db.flush()
