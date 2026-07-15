from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
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


def _queue_event(
    background_tasks: BackgroundTasks,
    db: Session,
    event_type: str,
    squad: SquadDetailRead,
    actor: User,
    *,
    data: dict | None = None,
) -> None:
    payload = {
        "id": squad.id,
        "name": squad.name,
        "slug": squad.slug,
        "fleet_id": squad.fleet_id,
        "member_count": squad.member_count,
        **(data or {}),
    }
    delivery_ids = queue_webhook_event_safely(
        db,
        event_type=event_type,
        resource_type="squad",
        resource_id=squad.id,
        resource_url=f"/squads/{squad.id}",
        actor=actor,
        scope_type="squad",
        scope_id=squad.id,
        fleet_id=squad.fleet_id,
        squad_id=squad.id,
        data=payload,
    )
    schedule_webhook_deliveries(background_tasks, delivery_ids)


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = create_squad(db, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    _queue_event(background_tasks, db, "squad.created", squad, current_user)
    return squad


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = update_squad(db, squad_id, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")
    _queue_event(background_tasks, db, "squad.updated", squad, current_user)
    return squad


@router.delete("/{squad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_squad(
    squad_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = get_squad(db, squad_id, current_user)
    try:
        archived = archive_squad(db, squad_id, current_user)
    except SquadPermissionError as exc:
        _raise_service_error(exc)
    if not archived or existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")
    _queue_event(background_tasks, db, "squad.archived", existing, current_user)


@router.post("/{squad_id}/members", response_model=SquadDetailRead, status_code=status.HTTP_201_CREATED)
def post_squad_member(
    squad_id: int,
    payload: SquadMemberCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = add_squad_member(db, squad_id, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad not found.")
    member = next(
        (row for row in squad.members if row.fleet_membership_id == payload.fleet_membership_id),
        None,
    )
    _queue_event(
        background_tasks,
        db,
        "squad.member.added",
        squad,
        current_user,
        data={
            "squad_name": squad.name,
            "member_display_name": member.display_name if member else "",
            "member_role": member.squad_role if member else payload.role,
        },
    )
    return squad


@router.put("/{squad_id}/members/{member_id}", response_model=SquadDetailRead)
def put_squad_member(
    squad_id: int,
    member_id: int,
    payload: SquadMemberUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = update_squad_member(db, squad_id, member_id, payload, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad member not found.")
    _queue_event(
        background_tasks,
        db,
        "squad.member.updated",
        squad,
        current_user,
        data={"squad_name": squad.name, "member_id": member_id},
    )
    return squad


@router.delete("/{squad_id}/members/{member_id}", response_model=SquadDetailRead)
def delete_squad_member(
    squad_id: int,
    member_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> SquadDetailRead:
    try:
        squad = remove_squad_member(db, squad_id, member_id, current_user)
    except (SquadPermissionError, SquadValidationError) as exc:
        _raise_service_error(exc)
    if squad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Squad member not found.")
    _queue_event(
        background_tasks,
        db,
        "squad.member.removed",
        squad,
        current_user,
        data={"squad_name": squad.name, "member_id": member_id},
    )
    return squad
