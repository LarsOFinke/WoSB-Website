from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.modules.ships.models.ship import Ship


def list_active_ships(db: Session) -> list[Ship]:
    return list(db.scalars(select(Ship).where(Ship.is_active.is_(True)).order_by(desc(Ship.rate), Ship.name)))


def get_ship(db: Session, ship_id: int) -> Ship | None:
    return db.get(Ship, ship_id)
