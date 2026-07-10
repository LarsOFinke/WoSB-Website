from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.builds.models.build import Build
from app.modules.groups.models.group import Group
from app.modules.groups.models.group_member import GroupMember
from app.modules.ships.models.ship import Ship
from app.modules.groups.models.group import GROUP_STATUS_CLOSED, GROUP_STATUS_OPEN, DEFAULT_GROUP_LIFETIME_HOURS
from app.modules.groups.schemas.group_create import GroupCreate
from app.modules.groups.schemas.group_join_request import GroupJoinRequest


class GroupValidationError(ValueError):
    pass


def _group_query():
    return select(Group).options(selectinload(Group.members).selectinload(GroupMember.ship))


def _normalize_like(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _refresh_group_status(group: Group) -> None:
    if group.status == GROUP_STATUS_CLOSED:
        return
    group.status = "full" if group.active_members_count >= group.max_members else GROUP_STATUS_OPEN


def list_groups(
    db: Session,
    search: str | None = None,
    focus: str | None = None,
    min_ship_rate: int | None = None,
    max_ship_rate: int | None = None,
) -> list[Group]:
    statement = _group_query().where(Group.status == GROUP_STATUS_OPEN)
    if search := _normalize_like(search):
        like = f"%{search}%"
        statement = statement.where(
            Group.title.ilike(like)
            | Group.focus.ilike(like)
            | Group.description.ilike(like)
            | Group.expectations.ilike(like)
            | Group.activity_plan.ilike(like)
            | Group.contact_note.ilike(like)
            | Group.fleet_restriction.ilike(like)
        )
    if focus := _normalize_like(focus):
        statement = statement.where(Group.focus == focus)
    if min_ship_rate is not None:
        # Ship-of-the-Line rates count down: 1 is strongest, 7 is lightest.
        # A group without an explicit strongest-rate cap behaves as if rate 1 is allowed.
        statement = statement.where(func.coalesce(Group.max_ship_rate, 1) <= min_ship_rate)
    if max_ship_rate is not None:
        # A group without an explicit weakest-rate cap behaves as if rate 7 is allowed.
        statement = statement.where(func.coalesce(Group.min_ship_rate, 7) >= max_ship_rate)
    statement = statement.order_by(Group.status.asc(), Group.expires_at.asc(), Group.created_at.desc())
    return list(db.scalars(statement).unique().all())


def list_user_groups(db: Session, owner_id: int, search: str | None = None) -> list[Group]:
    statement = _group_query().where(Group.owner_id == owner_id)
    if search := _normalize_like(search):
        like = f"%{search}%"
        statement = statement.where(
            Group.title.ilike(like)
            | Group.focus.ilike(like)
            | Group.description.ilike(like)
            | Group.expectations.ilike(like)
            | Group.activity_plan.ilike(like)
            | Group.contact_note.ilike(like)
        )
    statement = statement.order_by(Group.created_at.desc(), Group.id.desc())
    return list(db.scalars(statement).unique().all())


def get_group(db: Session, group_id: int) -> Group | None:
    group = db.scalar(_group_query().where(Group.id == group_id))
    if group is None:
        return None
    _refresh_group_status(group)
    db.commit()
    db.refresh(group)
    return group


def create_group(db: Session, payload: GroupCreate, owner_id: int) -> Group:
    group = Group(
        title=payload.title,
        focus=payload.focus,
        description=payload.description,
        expectations=payload.expectations,
        activity_plan=payload.activity_plan,
        contact_note=payload.contact_note,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        max_members=payload.max_members,
        min_ship_rate=payload.min_ship_rate,
        max_ship_rate=payload.max_ship_rate,
        allow_guests=payload.allow_guests,
        fleet_restriction=payload.fleet_restriction,
        owner_id=owner_id,
        expires_at=datetime.utcnow() + timedelta(hours=DEFAULT_GROUP_LIFETIME_HOURS),
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return get_group(db, group.id) or group


def close_group(db: Session, group_id: int, current_user: User) -> bool:
    group = get_group(db, group_id)
    if group is None:
        return False
    if group.owner_id != current_user.id and not current_user.can_moderate:
        raise GroupValidationError("You can only close your own groups.")
    if group.status != GROUP_STATUS_CLOSED:
        group.status = GROUP_STATUS_CLOSED
        group.closed_at = datetime.utcnow()
        db.commit()
    return True


def _rate_requirement_label(group: Group) -> str:
    if group.min_ship_rate and group.max_ship_rate:
        return f"rate {group.max_ship_rate} to {group.min_ship_rate}"
    if group.min_ship_rate:
        return f"rate {group.min_ship_rate} or better"
    if group.max_ship_rate:
        return f"rate {group.max_ship_rate} or worse"
    return "any rate"


def _ship_rate_allowed(group: Group, ship_rate: int | None) -> bool:
    if ship_rate is None:
        return group.min_ship_rate is None and group.max_ship_rate is None
    if group.min_ship_rate is not None and ship_rate > group.min_ship_rate:
        return False
    if group.max_ship_rate is not None and ship_rate < group.max_ship_rate:
        return False
    return True


def _requires_ship_rate(group: Group) -> bool:
    return group.min_ship_rate is not None or group.max_ship_rate is not None


def _require_joinable(group: Group, payload: GroupJoinRequest, current_user: User | None) -> None:
    _refresh_group_status(group)
    if group.status != GROUP_STATUS_OPEN:
        raise GroupValidationError("This group is not open for new members.")
    if group.spots_left <= 0:
        raise GroupValidationError("This group is already full.")
    if current_user is None and not group.allow_guests:
        raise GroupValidationError("This group only accepts signed-in members.")
    if current_user is not None:
        for member in group.members:
            if member.is_active and member.user_id == current_user.id:
                raise GroupValidationError("You already joined this group.")
    if _requires_ship_rate(group):
        requirement = _rate_requirement_label(group)
        if payload.ship_rate is None:
            raise GroupValidationError(f"This group requires a ship in the allowed range ({requirement}).")
        if not _ship_rate_allowed(group, payload.ship_rate):
            raise GroupValidationError(f"The selected ship is outside the allowed range ({requirement}).")


def _resolve_join_ship_and_build(
    db: Session,
    group: Group,
    payload: GroupJoinRequest,
    current_user: User | None,
) -> tuple[int | None, int | None, str | None, int | None]:
    build_id = payload.build_id
    ship_id = payload.ship_id
    ship_name = payload.ship_name
    ship_rate = payload.ship_rate

    if build_id is not None:
        if current_user is None:
            raise GroupValidationError("Build links require a signed-in account.")
        build = db.get(Build, build_id)
        if build is None or build.owner_id != current_user.id:
            raise GroupValidationError("The selected build does not belong to your account.")
        ship_id = build.ship_id
        ship_name = build.ship.name
        ship_rate = build.ship.rate

    if ship_id is not None and build_id is None:
        ship = db.get(Ship, ship_id)
        if ship is None or not ship.is_active:
            raise GroupValidationError("The selected ship does not exist.")
        ship_name = ship.name
        ship_rate = ship.rate

    if _requires_ship_rate(group) and not _ship_rate_allowed(group, ship_rate):
        requirement = _rate_requirement_label(group)
        raise GroupValidationError(f"The selected ship is outside the allowed range ({requirement}).")

    return build_id, ship_id, ship_name, ship_rate


def join_group(db: Session, group_id: int, payload: GroupJoinRequest, current_user: User | None) -> Group:
    group = get_group(db, group_id)
    if group is None:
        raise GroupValidationError("Group search not found.")

    build_id, ship_id, ship_name, ship_rate = _resolve_join_ship_and_build(db, group, payload, current_user)
    normalized_payload = payload.model_copy(update={
        "build_id": build_id,
        "ship_id": ship_id,
        "ship_name": ship_name,
        "ship_rate": ship_rate,
    })
    _require_joinable(group, normalized_payload, current_user)

    display_name = normalized_payload.display_name
    if current_user is not None and (not display_name or display_name == current_user.username):
        display_name = current_user.display_name

    member = GroupMember(
        group_id=group.id,
        user_id=current_user.id if current_user else None,
        is_guest=current_user is None,
        display_name=display_name,
        fleet_name=normalized_payload.fleet_name,
        ship_id=ship_id,
        build_id=build_id,
        ship_name=ship_name,
        ship_rate=ship_rate,
        note=normalized_payload.note,
    )
    db.add(member)
    db.flush()
    _refresh_group_status(group)
    db.commit()
    return get_group(db, group.id) or group
