from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.mortar_modification import ShipMortarModification
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.ship_upgrade_effect import ShipUpgradeEffectOverride
from app.modules.ships.models.weapon_mount import (
    ShipWeaponMount,
    WeaponClassDefinition,
    WeaponSlotType,
)
from app.modules.ships.models.rate_weapon_class import ShipRateWeaponClassRule
from app.bootstrap.catalog_loader import load_master_data_catalog, load_ship_seed_document
from app.bootstrap.catalog_sync import mark_seed_applied, seed_key, should_apply_seed


def seed_ship_catalog(db: Session) -> None:
    document = load_ship_seed_document()
    seed_weapon_definitions(db, document=document)
    seed_ship_rate_weapon_class_rules(db)
    seed_ships(db, document=document)


def seed_weapon_definitions(db: Session, *, document=None) -> None:
    document = document or load_ship_seed_document()
    for model, rows in (
        (WeaponClassDefinition, document.weapon_classes),
        (WeaponSlotType, document.weapon_slot_types),
    ):
        for row in rows:
            payload = row.model_dump(mode="json")
            existing = db.scalar(select(model).where(model.code == payload["code"]))
            if existing is None:
                db.add(model(**payload))
                continue
            for field_name, value in payload.items():
                setattr(existing, field_name, value)
    db.commit()


def seed_ship_rate_weapon_class_rules(db: Session) -> None:
    document = load_master_data_catalog().build_rules
    weapon_classes = {
        row.code: row for row in db.scalars(select(WeaponClassDefinition)).all()
    }
    for item in document.ship_rate_weapon_classes:
        weapon_class = weapon_classes.get(item.weapon_class)
        if weapon_class is None:
            raise ValueError(f"Unknown weapon class in rate rule: {item.weapon_class}")
        rule = db.get(ShipRateWeaponClassRule, item.rate)
        if rule is None:
            db.add(
                ShipRateWeaponClassRule(
                    rate=item.rate,
                    weapon_class_id=weapon_class.id,
                )
            )
        else:
            rule.weapon_class_id = weapon_class.id
    db.commit()

def seed_ships(db: Session, *, document=None) -> None:
    document = document or load_ship_seed_document()
    slot_types = {row.code: row for row in db.scalars(select(WeaponSlotType)).all()}
    weapon_classes = {
        row.code: row for row in db.scalars(select(WeaponClassDefinition)).all()
    }
    active_seed_keys: set[str] = set()

    for ship_data in document.ships:
        seed_payload = ship_data.model_dump(mode="json")
        raw_payload = dict(seed_payload)
        stable_id = raw_payload.pop("seed_id")
        normalized_mounts = list(raw_payload.pop("weapon_mounts"))
        mortar_modification = raw_payload.pop("mortar_modification")
        upgrade_effect_overrides = list(raw_payload.pop("upgrade_effect_overrides"))
        key = seed_key("ship", stable_id)
        active_seed_keys.add(key)
        canonical_payload = {
            **raw_payload,
            "mortar_modification": mortar_modification,
            "upgrade_effect_overrides": upgrade_effect_overrides,
            "weapon_mounts": normalized_mounts,
        }

        existing = db.scalar(select(Ship).where(Ship.seed_key == key))
        if existing is None:
            candidate = db.scalar(select(Ship).where(Ship.name == raw_payload["name"]))
            if candidate is not None and candidate.seed_revision == "custom":
                raise ValueError(
                    f"Custom ship {candidate.name!r} conflicts with seed key {key!r}. "
                    "Rename the custom record or assign a different seed_id."
                )
            existing = candidate
        if existing is None:
            existing = Ship(**raw_payload)
            db.add(existing)
            db.flush()
        elif existing.seed_key is None:
            existing.seed_key = key

        if not should_apply_seed(existing, payload=canonical_payload):
            continue

        for field_name, value in raw_payload.items():
            setattr(existing, field_name, value)
        _sync_mounts(
            existing,
            normalized_mounts,
            slot_types=slot_types,
            weapon_classes=weapon_classes,
        )
        _sync_mortar_modification(existing, mortar_modification)
        mark_seed_applied(existing, key=key, payload=canonical_payload)

    for ship in db.scalars(select(Ship).where(Ship.seed_key.is_not(None))).all():
        if ship.seed_key not in active_seed_keys and not ship.is_seed_overridden:
            ship.is_active = False
            ship.seed_revision = None
            ship.seed_checksum = None
    db.commit()


def seed_ship_upgrade_effect_overrides(db: Session, *, document=None) -> bool:
    """Synchronize sparse per-ship upgrade values after build options exist.

    The ship catalog may be seeded independently in focused tests and admin
    workflows. In that case build options are not necessarily present yet, so
    this function deliberately returns ``False`` without changing existing rows.
    A full bootstrap and ``seed_build_options`` call always retry the sync.
    """

    document = document or load_ship_seed_document()
    requested_seed_ids = {
        override.upgrade_seed_id
        for ship in document.ships
        for override in ship.upgrade_effect_overrides
    }
    if not requested_seed_ids:
        return True

    upgrade_effect_keys = {
        option.seed_id: set(option.stat_effects)
        for option_document in load_master_data_catalog().build_options
        if option_document.category == "upgrade"
        for option in option_document.items
    }
    missing_seed_definitions = sorted(requested_seed_ids.difference(upgrade_effect_keys))
    if missing_seed_definitions:
        raise ValueError(
            f"Unknown upgrade seed IDs in ship override catalog: {missing_seed_definitions}"
        )

    option_keys = {
        seed_key("build-option", "upgrade", stable_id): stable_id
        for stable_id in requested_seed_ids
    }
    options = db.scalars(
        select(BuildItemOption)
        .options(selectinload(BuildItemOption.effects))
        .where(BuildItemOption.seed_key.in_(option_keys))
    ).unique().all()
    if not options:
        return False

    options_by_seed_id = {
        option_keys[option.seed_key]: option
        for option in options
        if option.seed_key in option_keys
    }
    missing = sorted(requested_seed_ids.difference(options_by_seed_id))
    if missing:
        raise ValueError(f"Unknown seeded upgrade IDs in ship overrides: {missing}")

    ship_keys = {seed_key("ship", ship.seed_id): ship for ship in document.ships}
    ships_by_key = {
        ship.seed_key: ship
        for ship in db.scalars(
            select(Ship)
            .options(selectinload(Ship.upgrade_effect_overrides))
            .where(Ship.seed_key.in_(ship_keys))
        ).unique().all()
    }

    changed = False
    for ship_key, ship_seed in ship_keys.items():
        ship = ships_by_key.get(ship_key)
        if ship is None or ship.is_seed_overridden:
            continue

        desired: dict[tuple[int, str], float] = {}
        for override in ship_seed.upgrade_effect_overrides:
            option = options_by_seed_id[override.upgrade_seed_id]
            available_keys = upgrade_effect_keys[override.upgrade_seed_id]
            unknown_keys = sorted(set(override.stat_effects).difference(available_keys))
            if unknown_keys:
                raise ValueError(
                    f"Ship {ship_seed.name!r} overrides unknown effects for "
                    f"{option.name!r}: {unknown_keys}"
                )
            for effect_key, effect_value in override.stat_effects.items():
                desired[(option.id, effect_key)] = float(effect_value)

        current_rows = {
            (row.option_id, row.effect_key): row
            for row in ship.upgrade_effect_overrides
        }
        current = {key: float(row.effect_value) for key, row in current_rows.items()}
        if current == desired:
            continue

        for key, effect_value in sorted(desired.items()):
            row = current_rows.get(key)
            if row is None:
                option_id, effect_key = key
                ship.upgrade_effect_overrides.append(
                    ShipUpgradeEffectOverride(
                        option_id=option_id,
                        effect_key=effect_key,
                        effect_value=effect_value,
                    )
                )
            else:
                row.effect_value = effect_value
        for key, row in current_rows.items():
            if key not in desired:
                ship.upgrade_effect_overrides.remove(row)
        changed = True

    if changed:
        db.commit()
    return True


def _sync_mounts(
    ship: Ship,
    normalized_mounts: list[dict[str, object]],
    *,
    slot_types: dict[str, WeaponSlotType],
    weapon_classes: dict[str, WeaponClassDefinition],
) -> None:
    current = {mount.slot_type.code: mount for mount in ship.weapon_mounts}
    active_codes: set[str] = set()

    for mount_data in normalized_mounts:
        payload = dict(mount_data)
        code = str(payload.pop("slot_type"))
        class_code = payload.pop("max_weapon_class", None)
        active_codes.add(code)
        values = {
            **payload,
            "slot_type_id": slot_types[code].id,
            "max_weapon_class_id": weapon_classes[str(class_code)].id if class_code else None,
        }
        mount = current.get(code)
        if mount is None:
            ship.weapon_mounts.append(ShipWeaponMount(**values))
            continue
        for field_name, value in values.items():
            setattr(mount, field_name, value)

    for code, mount in current.items():
        if code not in active_codes:
            ship.weapon_mounts.remove(mount)


def _sync_mortar_modification(
    ship: Ship,
    payload: dict[str, object] | None,
) -> None:
    if payload is None:
        ship.mortar_modification = None
        return
    if ship.mortar_modification is None:
        ship.mortar_modification = ShipMortarModification(**payload)
        return
    for field_name, value in payload.items():
        setattr(ship.mortar_modification, field_name, value)
