from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUserId, DbSession
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services import ProfileNotFoundError, ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileRead)
def get_my_profile(db: DbSession, user_id: CurrentUserId) -> ProfileRead:
    try:
        return ProfileService(db).get_profile(user_id=user_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/me", response_model=ProfileRead)
def update_my_profile(payload: ProfileUpdate, db: DbSession, user_id: CurrentUserId) -> ProfileRead:
    try:
        return ProfileService(db).update_profile(payload, user_id=user_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
