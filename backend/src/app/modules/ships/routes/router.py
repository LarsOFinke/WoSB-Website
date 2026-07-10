from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.ships.schemas.ship import ShipRead
from app.modules.ships.services.ship_service import list_active_ships

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("", response_model=list[ShipRead])
def list_ships(db: Session = Depends(get_db)) -> list[ShipRead]:
    return list_active_ships(db)
