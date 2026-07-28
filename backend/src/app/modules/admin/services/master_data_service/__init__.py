from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.admin.schemas.master_data import (
    MasterDataCategoryCreate,
    MasterDataCategoryUpdate,
    MasterDataOptionCreate,
    MasterDataOptionUpdate,
    MasterDataShipCreate,
    MasterDataShipUpdate,
)

from .common import MasterDataError
from .service import MasterDataService


def master_data_overview(db: Session):
    return MasterDataService(db).overview()


def get_taxonomy(db: Session):
    return MasterDataService(db).taxonomy()


def restore_all_seed_defaults(db: Session):
    return MasterDataService(db).restore_seed_defaults()


def list_categories(db: Session):
    return MasterDataService(db).categories.list()


def create_category(db: Session, payload: MasterDataCategoryCreate):
    return MasterDataService(db).categories.create(payload)


def update_category(db: Session, category_id: int, payload: MasterDataCategoryUpdate):
    return MasterDataService(db).categories.update(category_id, payload)


def deactivate_category(db: Session, category_id: int) -> None:
    MasterDataService(db).categories.deactivate(category_id)


def restore_category_seed(db: Session, category_id: int):
    return MasterDataService(db).categories.restore_seed(category_id)


def list_options(db: Session, *, category_key: str | None = None, search: str | None = None):
    return MasterDataService(db).options.list(category_key=category_key, search=search)


def create_option(db: Session, payload: MasterDataOptionCreate):
    return MasterDataService(db).options.create(payload)


def update_option(db: Session, option_id: int, payload: MasterDataOptionUpdate):
    return MasterDataService(db).options.update(option_id, payload)


def deactivate_option(db: Session, option_id: int) -> None:
    MasterDataService(db).options.deactivate(option_id)


def restore_option_seed(db: Session, option_id: int):
    return MasterDataService(db).options.restore_seed(option_id)


def list_ships(db: Session, *, search: str | None = None):
    return MasterDataService(db).ships.list(search=search)


def create_ship(db: Session, payload: MasterDataShipCreate):
    return MasterDataService(db).ships.create(payload)


def update_ship(db: Session, ship_id: int, payload: MasterDataShipUpdate):
    return MasterDataService(db).ships.update(ship_id, payload)


def deactivate_ship(db: Session, ship_id: int) -> None:
    MasterDataService(db).ships.deactivate(ship_id)


def restore_ship_seed(db: Session, ship_id: int):
    return MasterDataService(db).ships.restore_seed(ship_id)


__all__ = [
    "MasterDataError",
    "MasterDataService",
    "create_category",
    "create_option",
    "create_ship",
    "deactivate_category",
    "deactivate_option",
    "deactivate_ship",
    "get_taxonomy",
    "list_categories",
    "list_options",
    "list_ships",
    "master_data_overview",
    "restore_all_seed_defaults",
    "restore_category_seed",
    "restore_option_seed",
    "restore_ship_seed",
    "update_category",
    "update_option",
    "update_ship",
]
