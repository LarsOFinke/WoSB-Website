from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.squads.schemas.squad import (
    SquadCreate,
    SquadDetailRead,
    SquadMemberCreate,
    SquadMemberUpdate,
    SquadRosterMemberRead,
    SquadSummaryRead,
    SquadUpdate,
)
from app.modules.squads.services.squad_service import (
    SquadPermissionError,
    SquadValidationError,
    add_squad_member,
    archive_squad,
    create_squad,
    get_squad,
    list_my_squads,
    list_squad_roster,
    list_squads,
    remove_squad_member,
    update_squad,
    update_squad_member,
)

router = APIRouter(prefix="/squads", tags=["fleet squads"])


def _raise_service_error(exc: Exception) -> None:
    if isinstance(exc, SquadPermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[SquadSummaryRead])
def get_squads(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[SquadSummaryRead]:
    return list_squads(db, current_user, include_inactive=include_inactive)


@router.get("/mine", response_model=list[SquadSummaryRead])
def get_my_squads(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[SquadSummaryRead]:
    return list_my_squads(db, current_user)


@router.get("/roster", response_model=list[SquadRosterMemberRead])
def get_squad_roster(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[SquadRosterMemberRead]:
    try:
        return list_squad_roster(db, current_user)
    except SquadPermissionError as exc:
        _raise_service_error(exc)


@router.post("", response_model=SquadDetailRead, status_code=status.HTTP_201_CREATED)
def post_squad(
    payload: SquadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        return create_squad(db, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)


@router.get("/{squad_id}", response_model=SquadDetailRead)
def get_squad_detail(
    squad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    squad = get_squad(db, squad_id, current_user)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")
    return squad


@router.put("/{squad_id}", response_model=SquadDetailRead)
def put_squad(
    squad_id: int,
    payload: SquadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = update_squad(db, squad_id, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")
    return squad


@router.delete("/{squad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_squad(
    squad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    try:
        archived = archive_squad(db, squad_id, current_user)
    except SquadPermissionError as exc:
        _raise_service_error(exc)
    if not archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")


@router.post("/{squad_id}/members", response_model=SquadDetailRead, status_code=status.HTTP_201_CREATED)
def post_squad_member(
    squad_id: int,
    payload: SquadMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = add_squad_member(db, squad_id, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")
    return squad


@router.put("/{squad_id}/members/{member_id}", response_model=SquadDetailRead)
def put_squad_member(
    squad_id: int,
    member_id: int,
    payload: SquadMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = update_squad_member(db, squad_id, member_id, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad member not found.")
    return squad


@router.delete("/{squad_id}/members/{member_id}", response_model=SquadDetailRead)
def delete_squad_member(
    squad_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = remove_squad_member(db, squad_id, member_id, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad member not found.")
    return squad
