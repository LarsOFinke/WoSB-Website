from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff, require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.onboarding.schemas.newcomer_guide import NewcomerGuideRead, NewcomerGuideUpdate
from app.modules.onboarding.services.newcomer_guide_service import (
    NewcomerGuideValidationError,
    get_newcomer_guide,
    update_newcomer_guide,
)

router = APIRouter(prefix="/newcomer-guide", tags=["newcomer-guide"])


@router.get("", response_model=NewcomerGuideRead)
def read_newcomer_guide(
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> NewcomerGuideRead:
    try:
        return get_newcomer_guide(db)
    except NewcomerGuideValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("", response_model=NewcomerGuideRead)
def replace_newcomer_guide(
    payload: NewcomerGuideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> NewcomerGuideRead:
    try:
        return update_newcomer_guide(db, payload, current_user)
    except NewcomerGuideValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
