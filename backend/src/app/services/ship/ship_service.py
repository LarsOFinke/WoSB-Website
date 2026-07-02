from sqlalchemy.orm import Session

from app.repositories import ShipRepository
from app.schemas.ship import ShipRead


class ShipService:
    def __init__(self, db: Session) -> None:
        self.ships = ShipRepository(db)

    def list_ships(
        self,
        *,
        rate: str | None = None,
        progression_class: str | None = None,
        ship_class: str | None = None,
        search: str | None = None,
    ) -> list[ShipRead]:
        return [
            ShipRead.model_validate(ship)
            for ship in self.ships.list(
                rate=rate,
                progression_class=progression_class,
                ship_class=ship_class,
                search=search,
            )
        ]

    def get_ship(self, ship_id: int) -> ShipRead | None:
        ship = self.ships.get(ship_id)
        return ShipRead.model_validate(ship) if ship else None
