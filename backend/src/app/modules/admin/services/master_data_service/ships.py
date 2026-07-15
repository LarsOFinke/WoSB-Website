from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.admin.schemas.master_data import (
    MasterDataShipCreate,
    MasterDataShipRead,
    MasterDataShipUpdate,
)
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.ship_upgrade_effect import ShipUpgradeEffectOverride
from app.modules.ships.models.weapon_mount import ShipWeaponMount
from app.seeds.catalog_sync import CUSTOM_MASTER_DATA_REVISION
from app.seeds.manager import SeedManager

from .common import MasterDataError, MasterDataUnitOfWork, TaxonomyRepository
from .mappers import MasterDataMapper


class ShipMasterDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._uow = MasterDataUnitOfWork(db)
        self._taxonomy = TaxonomyRepository(db)

    @staticmethod
    def query():
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

    def list(self, *, search: str | None = None) -> list[MasterDataShipRead]:
        query = self.query()
        if search:
            query = query.where(func.lower(Ship.name).contains(search.strip().casefold()))
        rows = self.db.scalars(
            query.order_by(Ship.rate, func.lower(Ship.name))
        ).unique().all()
        return [MasterDataMapper.ship(row) for row in rows]

    def create(self, payload: MasterDataShipCreate) -> MasterDataShipRead:
        row = Ship(
            name=payload.name,
            rate=payload.rate,
            ship_type=payload.ship_type,
            seed_revision=CUSTOM_MASTER_DATA_REVISION,
        )
        self.db.add(row)
        self._apply(row, payload)
        self._uow.commit("A ship with this name already exists.")
        return MasterDataMapper.ship(self._reload(row.id))

    def update(self, ship_id: int, payload: MasterDataShipUpdate) -> MasterDataShipRead:
        row = self._reload(ship_id, required=False)
        if row is None:
            raise MasterDataError("Ship not found.")
        self._apply(row, payload)
        if row.seed_key:
            row.is_seed_overridden = True
        self._uow.commit("A ship with this name already exists.")
        return MasterDataMapper.ship(self._reload(ship_id))

    def deactivate(self, ship_id: int) -> None:
        row = self.db.get(Ship, ship_id)
        if row is None:
            raise MasterDataError("Ship not found.")
        row.is_active = False
        if row.seed_key:
            row.is_seed_overridden = True
        self.db.commit()

    def restore_seed(self, ship_id: int) -> MasterDataShipRead:
        row = self.db.get(Ship, ship_id)
        if row is None or not row.seed_key:
            raise MasterDataError("This ship has no seed default.")
        seed_key = row.seed_key
        row.is_seed_overridden = False
        row.seed_revision = None
        row.seed_checksum = None
        row.upgrade_effect_overrides.clear()
        self.db.commit()
        SeedManager(self.db).seed_ships()
        restored = self.db.scalar(self.query().where(Ship.seed_key == seed_key))
        if restored is None:
            raise MasterDataError("Seed default no longer exists.")
        return MasterDataMapper.ship(restored)

    def _apply(
        self,
        row: Ship,
        payload: MasterDataShipCreate | MasterDataShipUpdate,
    ) -> None:
        weapon_classes, slot_types = self._taxonomy.maps()
        for field, value in payload.model_dump(
            exclude={"weapon_mounts", "upgrade_effect_overrides"}
        ).items():
            setattr(row, field, value)
        self._replace_mounts(row, payload.weapon_mounts, weapon_classes, slot_types)
        self._replace_upgrade_overrides(row, payload.upgrade_effect_overrides)

    @staticmethod
    def _replace_mounts(row: Ship, payloads: list, weapon_classes: dict, slot_types: dict) -> None:
        current = {mount.slot_type.code: mount for mount in row.weapon_mounts}
        active: set[str] = set()
        for payload in payloads:
            if payload.slot_type not in slot_types:
                raise MasterDataError(f"Unknown weapon slot type: {payload.slot_type}")
            if payload.max_weapon_class and payload.max_weapon_class not in weapon_classes:
                raise MasterDataError(f"Unknown weapon class: {payload.max_weapon_class}")
            active.add(payload.slot_type)
            mount = current.get(payload.slot_type)
            values = {
                "slot_type_id": slot_types[payload.slot_type].id,
                "capacity": payload.capacity,
                "max_weapon_class_id": (
                    weapon_classes[payload.max_weapon_class].id
                    if payload.max_weapon_class
                    else None
                ),
                "max_caliber_inches": payload.max_caliber_inches,
            }
            if mount is None:
                row.weapon_mounts.append(ShipWeaponMount(**values))
            else:
                for field, value in values.items():
                    setattr(mount, field, value)
        for code, mount in current.items():
            if code not in active:
                row.weapon_mounts.remove(mount)

    def _replace_upgrade_overrides(self, row: Ship, payloads: list) -> None:
        option_ids = [item.option_id for item in payloads]
        options = (
            {
                option.id: option
                for option in self.db.scalars(
                    select(BuildItemOption)
                    .options(selectinload(BuildItemOption.effects))
                    .join(BuildItemOption.category)
                    .where(BuildItemOption.id.in_(option_ids))
                ).unique().all()
            }
            if option_ids
            else {}
        )
        for item in payloads:
            option = options.get(item.option_id)
            if option is None:
                raise MasterDataError(f"Upgrade option {item.option_id} not found.")
            if option.category.key != "upgrade":
                raise MasterDataError(f"Option {item.option_id} is not an upgrade.")
        row.upgrade_effect_overrides.clear()
        for item in payloads:
            for effect_key, effect_value in item.stat_effects.items():
                row.upgrade_effect_overrides.append(
                    ShipUpgradeEffectOverride(
                        option_id=item.option_id,
                        effect_key=effect_key,
                        effect_value=float(effect_value),
                    )
                )

    def _reload(self, ship_id: int, *, required: bool = True) -> Ship | None:
        row = self.db.scalar(self.query().where(Ship.id == ship_id))
        if required and row is None:
            raise MasterDataError(f"Ship {ship_id} disappeared during reload.")
        return row
