from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.modules.admin.schemas.master_data import (
    MasterDataCategoryCreate,
    MasterDataCategoryRead,
    MasterDataCategoryUpdate,
    MasterDataOptionCreate,
    MasterDataOptionRead,
    MasterDataOptionUpdate,
    MasterDataOverview,
    MasterDataShipCreate,
    MasterDataShipMount,
    MasterDataShipRead,
    MasterDataShipUpgradeOverrideRead,
    MasterDataShipUpdate,
    MasterDataTaxonomyRead,
    WeaponClassRead,
    WeaponSlotTypeRead,
)
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.build_item_option_slot import BuildItemOptionSlotType
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.ship_upgrade_effect import ShipUpgradeEffectOverride
from app.modules.ships.models.weapon_mount import (
    ShipWeaponMount,
    WeaponClassDefinition,
    WeaponSlotType,
)
from app.seeds.catalog_sync import CUSTOM_MASTER_DATA_REVISION
from app.seeds.manager import SeedManager


class MasterDataError(ValueError):
    pass


def _seed_status(row: object) -> str:
    if not getattr(row, "seed_key", None):
        return "custom"
    if getattr(row, "is_seed_overridden", False):
        return "overridden"
    return "seeded"


def _category_read(row: BuildItemCategory) -> MasterDataCategoryRead:
    return MasterDataCategoryRead(
        id=row.id,
        key=row.key,
        label=row.label,
        sort_order=row.sort_order,
        is_active=row.is_active,
        seed_key=row.seed_key,
        seed_revision=row.seed_revision,
        is_seed_overridden=row.is_seed_overridden,
        seed_status=_seed_status(row),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _option_read(row: BuildItemOption) -> MasterDataOptionRead:
    return MasterDataOptionRead(
        id=row.id,
        category_id=row.category_id,
        category_key=row.category.key,
        category_label=row.category.label,
        name=row.name,
        source=row.source,
        notes=row.notes,
        image_url=row.image_url,
        option_kind=row.option_kind,
        weapon_class=row.weapon_class_code,
        weapon_caliber_inches=row.weapon_caliber_inches,
        stat_effects=row.stat_effects,
        allowed_slot_types=row.allowed_slots,
        sort_order=row.sort_order,
        is_active=row.is_active,
        seed_key=row.seed_key,
        seed_revision=row.seed_revision,
        is_seed_overridden=row.is_seed_overridden,
        seed_status=_seed_status(row),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _ship_read(row: Ship) -> MasterDataShipRead:
    mounts = [
        MasterDataShipMount(
            slot_type=mount.slot_type.code,
            capacity=mount.capacity,
            max_weapon_class=(mount.max_weapon_class.code if mount.max_weapon_class else None),
            max_caliber_inches=mount.max_caliber_inches,
        )
        for mount in sorted(row.weapon_mounts, key=lambda item: item.slot_type.sort_order)
    ]
    override_option_ids = sorted({item.option_id for item in row.upgrade_effect_overrides})
    overrides = []
    for option_id in override_option_ids:
        rows = [item for item in row.upgrade_effect_overrides if item.option_id == option_id]
        option = rows[0].option
        sparse = {item.effect_key: item.normalized_value for item in rows}
        overrides.append(
            MasterDataShipUpgradeOverrideRead(
                option_id=option.id,
                option_name=option.name,
                stat_effects=sparse,
                base_stat_effects=option.stat_effects,
                effective_stat_effects=effective_upgrade_effects(option, row),
            )
        )
    return MasterDataShipRead(
        id=row.id,
        name=row.name,
        rate=row.rate,
        ship_type=row.ship_type,
        durability=row.durability,
        speed_knots=row.speed_knots,
        maneuverability=row.maneuverability,
        armor=row.armor,
        hold_capacity=row.hold_capacity,
        crew_capacity=row.crew_capacity,
        sailor_minimum=row.sailor_minimum,
        displacement_tons=row.displacement_tons,
        source=row.source,
        image_url=row.image_url,
        sail_slots=row.sail_slots,
        upgrade_slots=row.upgrade_slots,
        has_lantern=row.has_lantern,
        is_active=row.is_active,
        weapon_mounts=mounts,
        upgrade_effect_overrides=overrides,
        weapon_layout=row.weapon_layout,
        seed_key=row.seed_key,
        seed_revision=row.seed_revision,
        is_seed_overridden=row.is_seed_overridden,
        seed_status=_seed_status(row),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _commit(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise MasterDataError(message) from exc


def master_data_overview(db: Session) -> MasterDataOverview:
    category_count = int(db.scalar(select(func.count(BuildItemCategory.id))) or 0)
    option_count = int(db.scalar(select(func.count(BuildItemOption.id))) or 0)
    ship_count = int(db.scalar(select(func.count(Ship.id))) or 0)
    overridden_count = sum(
        int(db.scalar(select(func.count(model.id)).where(model.is_seed_overridden.is_(True))) or 0)
        for model in (BuildItemCategory, BuildItemOption, Ship)
    )
    inactive_count = sum(
        int(db.scalar(select(func.count(model.id)).where(model.is_active.is_(False))) or 0)
        for model in (BuildItemCategory, BuildItemOption, Ship)
    )
    return MasterDataOverview(
        category_count=category_count,
        option_count=option_count,
        ship_count=ship_count,
        overridden_count=overridden_count,
        inactive_count=inactive_count,
    )


def list_categories(db: Session) -> list[MasterDataCategoryRead]:
    rows = db.scalars(
        select(BuildItemCategory).order_by(BuildItemCategory.sort_order, BuildItemCategory.label)
    ).all()
    return [_category_read(row) for row in rows]


def create_category(db: Session, payload: MasterDataCategoryCreate) -> MasterDataCategoryRead:
    row = BuildItemCategory(**payload.model_dump(), seed_revision=CUSTOM_MASTER_DATA_REVISION)
    db.add(row)
    _commit(db, "A category with this key already exists.")
    db.refresh(row)
    return _category_read(row)


def update_category(
    db: Session, category_id: int, payload: MasterDataCategoryUpdate
) -> MasterDataCategoryRead:
    row = db.get(BuildItemCategory, category_id)
    if row is None:
        raise MasterDataError("Category not found.")
    for field, value in payload.model_dump().items():
        setattr(row, field, value)
    if row.seed_key:
        row.is_seed_overridden = True
    _commit(db, "Category could not be updated.")
    db.refresh(row)
    return _category_read(row)


def deactivate_category(db: Session, category_id: int) -> None:
    row = db.get(BuildItemCategory, category_id)
    if row is None:
        raise MasterDataError("Category not found.")
    row.is_active = False
    if row.seed_key:
        row.is_seed_overridden = True
    db.commit()


def restore_category_seed(db: Session, category_id: int) -> MasterDataCategoryRead:
    row = db.get(BuildItemCategory, category_id)
    if row is None or not row.seed_key:
        raise MasterDataError("This category has no seed default.")
    seed_key_value = row.seed_key
    row.is_seed_overridden = False
    row.seed_revision = None
    row.seed_checksum = None
    db.commit()
    SeedManager(db).seed_build_options()
    restored = db.scalar(select(BuildItemCategory).where(BuildItemCategory.seed_key == seed_key_value))
    if restored is None:
        raise MasterDataError("Seed default no longer exists.")
    return _category_read(restored)


def _option_query():
    return select(BuildItemOption).options(
        selectinload(BuildItemOption.effects),
        selectinload(BuildItemOption.slot_type_links).selectinload(BuildItemOptionSlotType.slot_type),
    )


def list_options(
    db: Session, *, category_key: str | None = None, search: str | None = None
) -> list[MasterDataOptionRead]:
    query = _option_query().join(BuildItemOption.category)
    if category_key:
        query = query.where(BuildItemCategory.key == category_key)
    if search:
        query = query.where(func.lower(BuildItemOption.name).contains(search.strip().casefold()))
    rows = db.scalars(
        query.order_by(BuildItemCategory.sort_order, BuildItemOption.sort_order, func.lower(BuildItemOption.name))
    ).unique().all()
    return [_option_read(row) for row in rows]


def _taxonomy_maps(db: Session) -> tuple[dict[str, WeaponClassDefinition], dict[str, WeaponSlotType]]:
    classes = {row.code: row for row in db.scalars(select(WeaponClassDefinition)).all()}
    slots = {row.code: row for row in db.scalars(select(WeaponSlotType)).all()}
    return classes, slots


def _apply_option_payload(
    db: Session, row: BuildItemOption, payload: MasterDataOptionCreate | MasterDataOptionUpdate
) -> None:
    category = db.get(BuildItemCategory, payload.category_id)
    if category is None:
        raise MasterDataError("Category not found.")
    weapon_classes, slot_types = _taxonomy_maps(db)
    if payload.weapon_class and payload.weapon_class not in weapon_classes:
        raise MasterDataError("Unknown weapon class.")
    unknown_slots = set(payload.allowed_slot_types).difference(slot_types)
    if unknown_slots:
        raise MasterDataError(f"Unknown weapon slot types: {', '.join(sorted(unknown_slots))}")

    values = payload.model_dump(exclude={"stat_effects", "allowed_slot_types", "weapon_class"})
    for field, value in values.items():
        setattr(row, field, value)
    row.weapon_class_id = weapon_classes[payload.weapon_class].id if payload.weapon_class else None

    current_effects = {effect.effect_key: effect for effect in row.effects}
    for key, value in payload.stat_effects.items():
        effect = current_effects.pop(key, None)
        if effect is None:
            row.effects.append(BuildItemEffect(effect_key=key, effect_value=float(value)))
        else:
            effect.effect_value = float(value)
    for effect in current_effects.values():
        row.effects.remove(effect)

    current_slots = {link.slot_type.code: link for link in row.slot_type_links}
    for code in payload.allowed_slot_types:
        if code not in current_slots:
            row.slot_type_links.append(BuildItemOptionSlotType(slot_type_id=slot_types[code].id))
    for code, link in current_slots.items():
        if code not in payload.allowed_slot_types:
            row.slot_type_links.remove(link)


def create_option(db: Session, payload: MasterDataOptionCreate) -> MasterDataOptionRead:
    row = BuildItemOption(
        category_id=payload.category_id,
        name=payload.name,
        seed_revision=CUSTOM_MASTER_DATA_REVISION,
    )
    db.add(row)
    _apply_option_payload(db, row, payload)
    _commit(db, "An option with this name already exists in the category.")
    row = db.scalar(_option_query().where(BuildItemOption.id == row.id))
    assert row is not None
    return _option_read(row)


def update_option(
    db: Session, option_id: int, payload: MasterDataOptionUpdate
) -> MasterDataOptionRead:
    row = db.scalar(_option_query().where(BuildItemOption.id == option_id))
    if row is None:
        raise MasterDataError("Option not found.")
    _apply_option_payload(db, row, payload)
    if row.seed_key:
        row.is_seed_overridden = True
    _commit(db, "An option with this name already exists in the category.")
    row = db.scalar(_option_query().where(BuildItemOption.id == option_id))
    assert row is not None
    return _option_read(row)


def deactivate_option(db: Session, option_id: int) -> None:
    row = db.get(BuildItemOption, option_id)
    if row is None:
        raise MasterDataError("Option not found.")
    row.is_active = False
    if row.seed_key:
        row.is_seed_overridden = True
    db.commit()


def restore_option_seed(db: Session, option_id: int) -> MasterDataOptionRead:
    row = db.get(BuildItemOption, option_id)
    if row is None or not row.seed_key:
        raise MasterDataError("This option has no seed default.")
    seed_key_value = row.seed_key
    row.is_seed_overridden = False
    row.seed_revision = None
    row.seed_checksum = None
    db.commit()
    SeedManager(db).seed_build_options()
    restored = db.scalar(_option_query().where(BuildItemOption.seed_key == seed_key_value))
    if restored is None:
        raise MasterDataError("Seed default no longer exists.")
    return _option_read(restored)


def _ship_query():
    return select(Ship).options(
        selectinload(Ship.weapon_mounts).selectinload(ShipWeaponMount.slot_type),
        selectinload(Ship.weapon_mounts).selectinload(ShipWeaponMount.max_weapon_class),
        selectinload(Ship.upgrade_effect_overrides)
        .selectinload(ShipUpgradeEffectOverride.option)
        .selectinload(BuildItemOption.effects),
        selectinload(Ship.upgrade_effect_overrides)
        .selectinload(ShipUpgradeEffectOverride.option)
        .selectinload(BuildItemOption.category),
    )


def list_ships(db: Session, *, search: str | None = None) -> list[MasterDataShipRead]:
    query = _ship_query()
    if search:
        query = query.where(func.lower(Ship.name).contains(search.strip().casefold()))
    rows = db.scalars(query.order_by(Ship.rate, func.lower(Ship.name))).unique().all()
    return [_ship_read(row) for row in rows]


def _apply_ship_payload(
    db: Session, row: Ship, payload: MasterDataShipCreate | MasterDataShipUpdate
) -> None:
    weapon_classes, slot_types = _taxonomy_maps(db)
    values = payload.model_dump(exclude={"weapon_mounts", "upgrade_effect_overrides"})
    for field, value in values.items():
        setattr(row, field, value)

    current = {mount.slot_type.code: mount for mount in row.weapon_mounts}
    active: set[str] = set()
    for mount_payload in payload.weapon_mounts:
        if mount_payload.slot_type not in slot_types:
            raise MasterDataError(f"Unknown weapon slot type: {mount_payload.slot_type}")
        if mount_payload.max_weapon_class and mount_payload.max_weapon_class not in weapon_classes:
            raise MasterDataError(f"Unknown weapon class: {mount_payload.max_weapon_class}")
        active.add(mount_payload.slot_type)
        mount = current.get(mount_payload.slot_type)
        values = {
            "slot_type_id": slot_types[mount_payload.slot_type].id,
            "capacity": mount_payload.capacity,
            "max_weapon_class_id": (
                weapon_classes[mount_payload.max_weapon_class].id
                if mount_payload.max_weapon_class
                else None
            ),
            "max_caliber_inches": mount_payload.max_caliber_inches,
        }
        if mount is None:
            row.weapon_mounts.append(ShipWeaponMount(**values))
        else:
            for field, value in values.items():
                setattr(mount, field, value)
    for code, mount in current.items():
        if code not in active:
            row.weapon_mounts.remove(mount)

    option_ids = [item.option_id for item in payload.upgrade_effect_overrides]
    options = {
        option.id: option
        for option in db.scalars(
            select(BuildItemOption)
            .options(selectinload(BuildItemOption.effects))
            .join(BuildItemOption.category)
            .where(BuildItemOption.id.in_(option_ids))
        ).unique().all()
    } if option_ids else {}
    for item in payload.upgrade_effect_overrides:
        option = options.get(item.option_id)
        if option is None:
            raise MasterDataError(f"Upgrade option {item.option_id} not found.")
        if option.category.key != "upgrade":
            raise MasterDataError(f"Option {item.option_id} is not an upgrade.")

    row.upgrade_effect_overrides.clear()
    for item in payload.upgrade_effect_overrides:
        for effect_key, effect_value in item.stat_effects.items():
            row.upgrade_effect_overrides.append(
                ShipUpgradeEffectOverride(
                    option_id=item.option_id,
                    effect_key=effect_key,
                    effect_value=float(effect_value),
                )
            )


def create_ship(db: Session, payload: MasterDataShipCreate) -> MasterDataShipRead:
    row = Ship(
        name=payload.name,
        rate=payload.rate,
        ship_type=payload.ship_type,
        seed_revision=CUSTOM_MASTER_DATA_REVISION,
    )
    db.add(row)
    _apply_ship_payload(db, row, payload)
    _commit(db, "A ship with this name already exists.")
    row = db.scalar(_ship_query().where(Ship.id == row.id))
    assert row is not None
    return _ship_read(row)


def update_ship(db: Session, ship_id: int, payload: MasterDataShipUpdate) -> MasterDataShipRead:
    row = db.scalar(_ship_query().where(Ship.id == ship_id))
    if row is None:
        raise MasterDataError("Ship not found.")
    _apply_ship_payload(db, row, payload)
    if row.seed_key:
        row.is_seed_overridden = True
    _commit(db, "A ship with this name already exists.")
    row = db.scalar(_ship_query().where(Ship.id == ship_id))
    assert row is not None
    return _ship_read(row)


def deactivate_ship(db: Session, ship_id: int) -> None:
    row = db.get(Ship, ship_id)
    if row is None:
        raise MasterDataError("Ship not found.")
    row.is_active = False
    if row.seed_key:
        row.is_seed_overridden = True
    db.commit()


def restore_ship_seed(db: Session, ship_id: int) -> MasterDataShipRead:
    row = db.get(Ship, ship_id)
    if row is None or not row.seed_key:
        raise MasterDataError("This ship has no seed default.")
    seed_key_value = row.seed_key
    row.is_seed_overridden = False
    row.seed_revision = None
    row.seed_checksum = None
    row.upgrade_effect_overrides.clear()
    db.commit()
    SeedManager(db).seed_ships()
    restored = db.scalar(_ship_query().where(Ship.seed_key == seed_key_value))
    if restored is None:
        raise MasterDataError("Seed default no longer exists.")
    return _ship_read(restored)


def get_taxonomy(db: Session) -> MasterDataTaxonomyRead:
    classes = db.scalars(select(WeaponClassDefinition).order_by(WeaponClassDefinition.rank)).all()
    slots = db.scalars(select(WeaponSlotType).order_by(WeaponSlotType.sort_order)).all()
    return MasterDataTaxonomyRead(
        weapon_classes=[WeaponClassRead(code=row.code, label=row.label, rank=row.rank) for row in classes],
        weapon_slot_types=[
            WeaponSlotTypeRead(code=row.code, label=row.label, sort_order=row.sort_order) for row in slots
        ],
    )
