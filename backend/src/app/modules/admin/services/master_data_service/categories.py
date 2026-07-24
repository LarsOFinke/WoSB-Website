from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.admin.schemas.master_data import (
    MasterDataCategoryCreate,
    MasterDataCategoryRead,
    MasterDataCategoryUpdate,
)
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.bootstrap.catalog_sync import CUSTOM_MASTER_DATA_REVISION
from app.bootstrap.manager import SeedManager

from .common import MasterDataError, MasterDataUnitOfWork
from .mappers import MasterDataMapper


class CategoryMasterDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._uow = MasterDataUnitOfWork(db)

    def list(self) -> list[MasterDataCategoryRead]:
        rows = self.db.scalars(
            select(BuildItemCategory).order_by(
                BuildItemCategory.sort_order, BuildItemCategory.label
            )
        ).all()
        return [MasterDataMapper.category(row) for row in rows]

    def create(self, payload: MasterDataCategoryCreate) -> MasterDataCategoryRead:
        row = BuildItemCategory(**payload.model_dump(), seed_revision=CUSTOM_MASTER_DATA_REVISION)
        self.db.add(row)
        self._uow.commit("A category with this key already exists.")
        self.db.refresh(row)
        return MasterDataMapper.category(row)

    def update(
        self, category_id: int, payload: MasterDataCategoryUpdate
    ) -> MasterDataCategoryRead:
        row = self._required(category_id)
        for field, value in payload.model_dump().items():
            setattr(row, field, value)
        if row.seed_key:
            row.is_seed_overridden = True
        self._uow.commit("Category could not be updated.")
        self.db.refresh(row)
        return MasterDataMapper.category(row)

    def deactivate(self, category_id: int) -> None:
        row = self._required(category_id)
        row.is_active = False
        if row.seed_key:
            row.is_seed_overridden = True
        self.db.commit()

    def restore_seed(self, category_id: int) -> MasterDataCategoryRead:
        row = self._required(category_id)
        if not row.seed_key:
            raise MasterDataError("This category has no seed default.")
        seed_key = row.seed_key
        row.is_seed_overridden = False
        row.seed_revision = None
        row.seed_checksum = None
        self.db.commit()
        SeedManager(self.db).seed_build_options()
        restored = self.db.scalar(
            select(BuildItemCategory).where(BuildItemCategory.seed_key == seed_key)
        )
        if restored is None:
            raise MasterDataError("Seed default no longer exists.")
        return MasterDataMapper.category(restored)

    def _required(self, category_id: int) -> BuildItemCategory:
        row = self.db.get(BuildItemCategory, category_id)
        if row is None:
            raise MasterDataError("Category not found.")
        return row
