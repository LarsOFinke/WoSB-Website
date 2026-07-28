from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope
from app.modules.groups.schemas.group_create import GroupCreate
from app.modules.groups.schemas.group_join_request import GroupJoinRequest
from app.modules.groups.schemas.group_read import GroupRead
from app.modules.groups.schemas.group_member_read import GroupMemberRead
from app.modules.groups.services.group_service import (
    GroupValidationError,
    close_group,
    create_group,
    get_group,
    join_group,
    list_groups,
    list_user_groups,
)

router = APIRouter(prefix="/groups", tags=["groups"])


def _group_event_data(group: GroupRead) -> dict:
    return {
        "id": group.id,
        "title": group.title,
        "focus": group.focus,
        "status": group.status,
        "max_members": group.max_members,
        "active_members_count": group.active_members_count,
        "spots_left": group.spots_left,
        "min_ship_rate": group.min_ship_rate,
        "max_ship_rate": group.max_ship_rate,
        "allow_guests": group.allow_guests,
        "fleet_restriction": group.fleet_restriction,
        "scheduled_start_at": group.scheduled_start_at,
        "scheduled_end_at": group.scheduled_end_at,
        "expires_at": group.expires_at,
        "owner": {"id": group.owner.id, "display_name": group.owner.display_name},
    }


def _queue_group_event(
    background_tasks: BackgroundTasks,
    db: Session,
    event_type: str,
    group: GroupRead,
    actor: User,
    *,
    member: GroupMemberRead | None = None,
) -> None:
    data = _group_event_data(group)
    if member is not None:
        data["member"] = {
            "id": member.id,
            "display_name": member.display_name,
            "fleet_name": member.fleet_name,
            "ship_name": member.ship_name,
            "ship_rate": member.ship_rate,
            "is_guest": member.is_guest,
        }
    owner = db.get(User, group.owner_id)
    owner_fleet_id = owner.fleet_id if owner is not None else None
    delivery_ids = queue_webhook_event_safely(
        db,
        event_type=event_type,
        resource_type="group",
        resource_id=group.id,
        resource_url=f"/groups/{group.id}",
        actor=actor,
        data=data,
        # Group-search events belong to the listing owner's fleet. Using the
        # joining or moderating actor here would route member/close events to
        # the wrong fleet-scoped webhook whenever actor and owner differ.
        **webhook_event_scope(db, fleet_id=owner_fleet_id),
    )
    schedule_webhook_deliveries(background_tasks, delivery_ids)


def _joined_member(group: GroupRead, user_id: int) -> GroupMemberRead | None:
    matches = [member for member in group.members if member.user_id == user_id and member.is_active]
    return max(matches, key=lambda member: (member.joined_at, member.id), default=None)


@router.get("", response_model=list[GroupRead])
def get_groups(
    search: str | None = Query(default=None, max_length=120),
    focus: str | None = Query(default=None, max_length=80),
    min_ship_rate: int | None = Query(default=None, ge=1, le=7),
    max_ship_rate: int | None = Query(default=None, ge=1, le=7),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[GroupRead]:
    if min_ship_rate is not None and max_ship_rate is not None and max_ship_rate > min_ship_rate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum rate must be numerically lower than or equal to minimum rate.")
    return list_groups(db, search=search, focus=focus, min_ship_rate=min_ship_rate, max_ship_rate=max_ship_rate)


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def post_group(
    group: GroupCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> GroupRead:
    created = GroupRead.model_validate(create_group(db, group, owner_id=current_user.id))
    _queue_group_event(background_tasks, db, "group.created", created, current_user)
    return created


@router.get("/mine", response_model=list[GroupRead])
def get_my_groups(
    search: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[GroupRead]:
    return list_user_groups(db, current_user.id, search=search)


@router.get("/{group_id}", response_model=GroupRead)
def get_group_detail(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> GroupRead:
    group = get_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    return group


@router.post("/{group_id}/join", response_model=GroupRead)
def post_group_join(
    group_id: int,
    payload: GroupJoinRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> GroupRead:
    try:
        joined = GroupRead.model_validate(join_group(db, group_id, payload, current_user))
    except GroupValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    _queue_group_event(
        background_tasks,
        db,
        "group.member.joined",
        joined,
        current_user,
        member=_joined_member(joined, current_user.id),
    )
    return joined


@router.post("/{group_id}/close", status_code=status.HTTP_204_NO_CONTENT)
def post_group_close(
    group_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = get_group(db, group_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    was_closed = existing.status == "closed"
    try:
        closed = close_group(db, group_id, current_user)
    except GroupValidationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not closed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
    if not was_closed:
        closed_group = GroupRead.model_validate(get_group(db, group_id))
        _queue_group_event(background_tasks, db, "group.closed", closed_group, current_user)
