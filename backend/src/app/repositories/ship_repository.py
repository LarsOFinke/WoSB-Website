from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ship


class ShipRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, ship_id: int) -> Ship | None:
        return self.db.get(Ship, ship_id)

    def get_by_name(self, name: str) -> Ship | None:
        stmt = select(Ship).where(Ship.name.ilike(name))
        return self.db.scalars(stmt).first()

    def list(
        self,
        *,
        rate: str | None = None,
        progression_class: str | None = None,
        ship_class: str | None = None,
        search: str | None = None,
        limit: int = 200,
    ) -> list[Ship]:
        stmt = select(Ship).order_by(Ship.progression_class, Ship.rate, Ship.name)
        if rate:
            stmt = stmt.where(Ship.rate == rate.upper())
        if progression_class:
            stmt = stmt.where(Ship.progression_class.ilike(progression_class))
        if ship_class:
            stmt = stmt.where(Ship.ship_class.ilike(ship_class))
        if search:
            stmt = stmt.where(Ship.name.ilike(f"%{search}%"))
        return list(self.db.scalars(stmt.limit(limit)).all())
