from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_staff
from app.db.session import get_db
from app.models import User
from app.models.user import ROLE_MODERATOR
from app.schemas import BuildRead, ForumThreadSummary, GuideSummary, ModeratorCreate, ModeratorCreateResponse, UserRead
from app.services.auth_service import AuthError, create_user
from app.services.build_service import delete_build, list_builds
from app.services.forum_service import delete_thread, list_threads
from app.services.guide_service import delete_guide, list_guides

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


@router.get("/forum/threads", response_model=list[ForumThreadSummary])
def admin_list_forum_threads(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[ForumThreadSummary]:
    return list_threads(db, search=search, category=category)


@router.delete("/forum/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_forum_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    if not delete_thread(db, thread_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum thread not found.")


@router.get("/guides", response_model=list[GuideSummary])
def admin_list_guides(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[GuideSummary]:
    return list_guides(db, search=search, category=category)


@router.delete("/guides/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_guide(
    guide_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    if not delete_guide(db, guide_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")


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
