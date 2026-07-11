from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.accounts.schemas.profile_update import ProfileUpdate
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.accounts.services.profile_service import ProfileValidationError, update_profile
from app.modules.permissions.models.role import FleetRoleDefinition
from app.modules.ships.models.ship import Ship

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserRead)
def get_profile(current_user: User = Depends(require_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/preferences/options")
def get_preference_options(
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> dict:
    ships = db.scalars(select(Ship).where(Ship.is_active.is_(True)).order_by(Ship.rate, Ship.name)).all()
    roles = db.scalars(select(FleetRoleDefinition).order_by(FleetRoleDefinition.rank.desc(), FleetRoleDefinition.label)).all()
    return {
        "ships": [{"id": ship.id, "name": ship.name, "rate": ship.rate} for ship in ships],
        "roles": [{"id": role.id, "code": role.code, "label": role.label} for role in roles],
    }


@router.put("", response_model=UserRead)
def put_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> UserRead:
    try:
        return UserRead.model_validate(update_profile(db, current_user, payload))
    except ProfileValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
