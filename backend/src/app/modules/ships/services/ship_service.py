from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.modules.ships.models.ship import Ship
from app.modules.ships.models.weapon_mount import ShipWeaponMount


def list_active_ships(db: Session) -> list[Ship]:
    statement = (
        select(Ship)
        .options(
            selectinload(Ship.weapon_mounts).selectinload(ShipWeaponMount.slot_type),
            selectinload(Ship.weapon_mounts).selectinload(ShipWeaponMount.max_weapon_class),
        )
        .where(Ship.is_active.is_(True))
        .order_by(desc(Ship.rate), Ship.name)
    )
    return list(db.scalars(statement).unique().all())


def get_ship(db: Session, ship_id: int) -> Ship | None:
    return db.get(Ship, ship_id)
