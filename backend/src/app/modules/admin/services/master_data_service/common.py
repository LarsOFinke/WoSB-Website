from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.ships.models.weapon_mount import WeaponClassDefinition, WeaponSlotType


class MasterDataError(ValueError):
    pass


class MasterDataUnitOfWork:
    def __init__(self, db: Session) -> None:
        self.db = db

    def commit(self, message: str) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise MasterDataError(message) from exc


class TaxonomyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def maps(self) -> tuple[dict[str, WeaponClassDefinition], dict[str, WeaponSlotType]]:
        classes = {row.code: row for row in self.db.scalars(select(WeaponClassDefinition)).all()}
        slots = {row.code: row for row in self.db.scalars(select(WeaponSlotType)).all()}
        return classes, slots


def seed_status(row: object) -> str:
    if not getattr(row, "seed_key", None):
        return "custom"
    if getattr(row, "is_seed_overridden", False):
        return "overridden"
    return "seeded"
