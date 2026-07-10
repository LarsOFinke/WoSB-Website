from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.accounts.schemas.profile_update import ProfileUpdate
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.accounts.services.profile_service import update_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserRead)
def get_profile(current_user: User = Depends(require_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.put("", response_model=UserRead)
def put_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> UserRead:
    return UserRead.model_validate(update_profile(db, current_user, payload))
