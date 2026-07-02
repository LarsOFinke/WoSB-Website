from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DbSession
from app.schemas.ship import ShipRead
from app.services import ShipService

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("", response_model=list[ShipRead])
def list_ships(
    db: DbSession,
    rate: str | None = Query(default=None, description="Roman rate, e.g. I, II, VII"),
    progression_class: str | None = Query(default=None, description="Fast, Combat, Transport, Heavy, Siege, Imperial"),
    ship_class: str | None = Query(default=None, description="e.g. Ship of the Line, Frigate"),
    search: str | None = Query(default=None, description="Case-insensitive search by ship name"),
) -> list[ShipRead]:
    return ShipService(db).list_ships(
        rate=rate,
        progression_class=progression_class,
        ship_class=ship_class,
        search=search,
    )


@router.get("/{ship_id}", response_model=ShipRead)
def get_ship(ship_id: int, db: DbSession) -> ShipRead:
    ship = ShipService(db).get_ship(ship_id)
    if not ship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schiff nicht gefunden.")
    return ship
