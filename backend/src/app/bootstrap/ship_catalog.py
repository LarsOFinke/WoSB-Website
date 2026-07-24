from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ships.models.mortar_modification import ShipMortarModification
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.weapon_mount import (
    ShipWeaponMount,
    WeaponClassDefinition,
    WeaponSlotType,
)
from app.bootstrap.catalog_loader import load_ship_seed_document
from app.bootstrap.catalog_sync import mark_seed_applied, seed_key, should_apply_seed


def seed_ship_catalog(db: Session) -> None:
    document = load_ship_seed_document()
    seed_weapon_definitions(db, document=document)
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
        key = seed_key("ship", stable_id)
        active_seed_keys.add(key)
        canonical_payload = {
            **raw_payload,
            "mortar_modification": mortar_modification,
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
