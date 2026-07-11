from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ships.models.ship import Ship
from app.modules.ships.models.weapon_mount import (
    ShipWeaponMount,
    WeaponClassDefinition,
    WeaponSlotType,
)
from app.seeds.build_catalog_quality import validate_ship_seed_data
from app.seeds.catalog_sync import mark_seed_applied, seed_key, should_apply_seed
from app.seeds.ships import SHIP_SEED_DATA
from app.seeds.weapon_mounts import WEAPON_CLASS_DATA, WEAPON_SLOT_TYPE_DATA, parse_weapon_layout


def seed_ship_catalog(db: Session) -> None:
    seed_weapon_definitions(db)
    seed_ships(db)


def seed_weapon_definitions(db: Session) -> None:
    for model, rows in (
        (WeaponClassDefinition, WEAPON_CLASS_DATA),
        (WeaponSlotType, WEAPON_SLOT_TYPE_DATA),
    ):
        for row in rows:
            existing = db.scalar(select(model).where(model.code == row["code"]))
            if existing is None:
                db.add(model(**row))
                continue
            for field_name, value in row.items():
                setattr(existing, field_name, value)
    db.commit()


def seed_ships(db: Session) -> None:
    validate_ship_seed_data(SHIP_SEED_DATA)
    slot_types = {row.code: row for row in db.scalars(select(WeaponSlotType)).all()}
    weapon_classes = {
        row.code: row for row in db.scalars(select(WeaponClassDefinition)).all()
    }
    active_seed_keys: set[str] = set()

    for ship_data in SHIP_SEED_DATA:
        raw_payload = dict(ship_data)
        stable_id = raw_payload.pop("seed_id", raw_payload["name"])
        layout = str(raw_payload.pop("weapon_layout", ""))
        max_weapon_class = raw_payload.pop("max_weapon_class", None)
        special_weapon_capacity = int(raw_payload.pop("special_weapon_capacity", 0) or 0)
        raw_payload.setdefault("image_url", None)
        key = seed_key("ship", stable_id)
        active_seed_keys.add(key)
        normalized_mounts = [
            dict(mount_data)
            for mount_data in parse_weapon_layout(
                layout,
                rate=int(raw_payload["rate"]),
                max_weapon_class=str(max_weapon_class) if max_weapon_class else None,
                special_weapon_capacity=special_weapon_capacity,
            )
        ]
        canonical_payload = {**raw_payload, "weapon_mounts": normalized_mounts}

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
