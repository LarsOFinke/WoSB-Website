from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_staff
from app.db.session import get_db
from app.models import User
from app.models.user import ROLE_MODERATOR
from app.schemas import BuildRead, ModeratorCreate, ModeratorCreateResponse, UserRead
from app.services.auth_service import AuthError, create_user
from app.services.build_service import delete_build, list_builds

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/builds", response_model=list[BuildRead])
def admin_list_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[BuildRead]:
    return list_builds(db, search=search, build_type=build_type)


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_build(
    build_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    deleted = delete_build(db, build_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[UserRead]:
    users = db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all()
    return [UserRead.model_validate(user) for user in users]


@router.post("/moderators", response_model=ModeratorCreateResponse, status_code=status.HTTP_201_CREATED)
def admin_create_moderator(
    payload: ModeratorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ModeratorCreateResponse:
    try:
        user = create_user(
            db,
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            role=ROLE_MODERATOR,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ModeratorCreateResponse(user=UserRead.model_validate(user))
