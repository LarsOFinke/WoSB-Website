from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.ships.schemas.ship import ShipRead
from app.modules.ships.services.ship_service import list_active_ships

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("", response_model=list[ShipRead])
def list_ships(
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[ShipRead]:
    return list_active_ships(db)
