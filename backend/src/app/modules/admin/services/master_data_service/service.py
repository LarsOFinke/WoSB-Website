from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.admin.schemas.master_data import (
    MasterDataOverview,
    MasterDataSeedRestoreSummary,
    MasterDataTaxonomyRead,
    WeaponClassRead,
    WeaponSlotTypeRead,
)
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.weapon_mount import WeaponClassDefinition, WeaponSlotType

from .categories import CategoryMasterDataService
from .options import OptionMasterDataService
from .ships import ShipMasterDataService


class MasterDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.categories = CategoryMasterDataService(db)
        self.options = OptionMasterDataService(db)
        self.ships = ShipMasterDataService(db)

    def overview(self) -> MasterDataOverview:
        category_count = self._count(BuildItemCategory)
        option_count = self._count(BuildItemOption)
        ship_count = self._count(Ship)
        models = (BuildItemCategory, BuildItemOption, Ship)
        return MasterDataOverview(
            category_count=category_count,
            option_count=option_count,
            ship_count=ship_count,
            overridden_count=sum(
                self._count(model, model.is_seed_overridden.is_(True)) for model in models
            ),
            inactive_count=sum(
                self._count(model, model.is_active.is_(False)) for model in models
            ),
        )

    def restore_seed_defaults(self) -> MasterDataSeedRestoreSummary:
        """Restore every repository-owned master-data record from the seed catalog.

        Local records are identified by a missing ``seed_key`` and remain untouched.
        The reset deliberately covers only the master-data workspace (categories,
        options, ships and their related catalog rows), not users, fleets or content.
        """

        from app.bootstrap.manager import SeedManager

        manager = SeedManager(self.db)
        restored = manager.restore_repository_seed_defaults()
        manager.seed_weapon_slot_types()
        manager.seed_build_options()
        manager.seed_ships()
        categories = self._count(BuildItemCategory, BuildItemCategory.seed_key.is_not(None))
        options = self._count(BuildItemOption, BuildItemOption.seed_key.is_not(None))
        ships = self._count(Ship, Ship.seed_key.is_not(None))
        return MasterDataSeedRestoreSummary(
            categories=categories,
            options=options,
            ships=ships,
            total=categories + options + ships,
            overrides_discarded=sum(restored.values()),
            custom_records_preserved=True,
        )

    def taxonomy(self) -> MasterDataTaxonomyRead:
        classes = self.db.scalars(
            select(WeaponClassDefinition).order_by(WeaponClassDefinition.rank)
        ).all()
        slots = self.db.scalars(
            select(WeaponSlotType).order_by(WeaponSlotType.sort_order)
        ).all()
        return MasterDataTaxonomyRead(
            weapon_classes=[
                WeaponClassRead(code=row.code, label=row.label, rank=row.rank)
                for row in classes
            ],
            weapon_slot_types=[
                WeaponSlotTypeRead(
                    code=row.code, label=row.label, sort_order=row.sort_order
                )
                for row in slots
            ],
        )

    def _count(self, model: type, condition=None) -> int:
        query = select(func.count(model.id))
        if condition is not None:
            query = query.where(condition)
        return int(self.db.scalar(query) or 0)
