from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_user
from app.db.session import get_db
from app.models import User
from app.schemas import GroupCreate, GroupJoinRequest, GroupRead
from app.services.group_service import (
    GroupValidationError,
    close_group,
    create_group,
    get_group,
    join_group,
    list_groups,
    list_user_groups,
)

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupRead])
def get_groups(
    search: str | None = Query(default=None, max_length=120),
    focus: str | None = Query(default=None, max_length=80),
    min_ship_rate: int | None = Query(default=None, ge=1, le=7),
    max_ship_rate: int | None = Query(default=None, ge=1, le=7),
    db: Session = Depends(get_db),
) -> list[GroupRead]:
    if min_ship_rate is not None and max_ship_rate is not None and max_ship_rate > min_ship_rate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum rate must be numerically lower than or equal to minimum rate.")
    return list_groups(db, search=search, focus=focus, min_ship_rate=min_ship_rate, max_ship_rate=max_ship_rate)


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def post_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> GroupRead:
    return create_group(db, group, owner_id=current_user.id)


@router.get("/mine", response_model=list[GroupRead])
def get_my_groups(
    search: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[GroupRead]:
    return list_user_groups(db, current_user.id, search=search)


@router.get("/{group_id}", response_model=GroupRead)
def get_group_detail(group_id: int, db: Session = Depends(get_db)) -> GroupRead:
    group = get_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    return group


@router.post("/{group_id}/join", response_model=GroupRead)
def post_group_join(
    group_id: int,
    payload: GroupJoinRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> GroupRead:
    try:
        return join_group(db, group_id, payload, current_user)
    except GroupValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{group_id}/close", status_code=status.HTTP_204_NO_CONTENT)
def post_group_close(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    try:
        closed = close_group(db, group_id, current_user)
    except GroupValidationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not closed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
