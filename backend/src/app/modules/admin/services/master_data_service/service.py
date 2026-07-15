from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.admin.schemas.master_data import (
    MasterDataOverview,
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
