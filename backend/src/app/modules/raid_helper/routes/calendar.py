from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.raid_helper.schemas.raid_helper import RaidHelperOptionDestination
from app.modules.raid_helper.services.raid_helper_service import RaidHelperError, integration_options

router = APIRouter(prefix="/calendar/raid-helper", tags=["calendar-raid-helper"])


@router.get("/options", response_model=list[RaidHelperOptionDestination])
def options(
    category: str = Query(max_length=80),
    squad_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    try:
        return integration_options(db, current_user, category=category, squad_id=squad_id)
    except RaidHelperError as exc:
        raise HTTPException(status_code=400 if "Invalid" in str(exc) else 403, detail=str(exc)) from exc
