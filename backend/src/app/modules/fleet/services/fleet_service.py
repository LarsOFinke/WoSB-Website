from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.models.fleet import (
    FLEET_MEMBER_ACTIVE,
    FLEET_MEMBER_PENDING,
    FLEET_MEMBER_STATUSES,
    FLEET_ROLE_ADMIRAL,
    FLEET_ROLE_MEMBER,
)
from app.modules.fleet.schemas.fleet_create import FleetCreate
from app.modules.fleet.schemas.fleet_join_request import FleetJoinRequest
from app.modules.fleet.schemas.fleet_membership_update import FleetMembershipUpdate
from app.modules.fleet.schemas.fleet_update import FleetUpdate
from app.modules.fleet.services.fleet_management_policy import validate_membership_update
from app.modules.permissions.models.role import FleetRoleDefinition
from app.modules.permissions.services.role_service import assign_fleet_role_definition, get_fleet_role

PRIMARY_FLEET_SLUG = "royal-blackwater-fleet"


class FleetValidationError(ValueError):
    pass


def sync_user_primary_fleet(
    db: Session,
    user: User,
    *,
    preferred_membership: FleetMembership | None = None,
    force_preferred: bool = False,
) -> User:
    """Compatibility no-op after removing the denormalized profile pointer."""

    del db, preferred_membership, force_preferred
    return user


def get_primary_fleet(db: Session, *, include_members: bool = False) -> Fleet | None:
    query = select(Fleet).where(Fleet.slug == PRIMARY_FLEET_SLUG)
    if include_members:
        query = query.options(
            selectinload(Fleet.memberships).selectinload(FleetMembership.user),
            selectinload(Fleet.memberships).selectinload(FleetMembership.fleet_role),
        )
    fleet = db.scalar(query)
    if fleet is None:
        fallback = select(Fleet).where(Fleet.is_active.is_(True)).order_by(Fleet.sort_order, Fleet.id)
        if include_members:
            fallback = fallback.options(
                selectinload(Fleet.memberships).selectinload(FleetMembership.user),
                selectinload(Fleet.memberships).selectinload(FleetMembership.fleet_role),
                )
        fleet = db.scalar(fallback)
    if fleet is None:
        return None
    _attach_summary(db, [fleet])
    if include_members:
        fleet.memberships = sorted(
            fleet.memberships,
            key=lambda item: (
                item.status != FLEET_MEMBER_PENDING,
                item.status != FLEET_MEMBER_ACTIVE,
                -item.role_rank,
                item.user.display_name.casefold(),
            ),
        )
    return fleet


def _summary_counts(db: Session) -> dict[int, tuple[int, int]]:
    rows = db.execute(
        select(FleetMembership.fleet_id, FleetMembership.status, func.count(FleetMembership.id))
        .group_by(FleetMembership.fleet_id, FleetMembership.status)
    ).all()
    counts: dict[int, list[int]] = {}
    for fleet_id, status, count in rows:
        active, pending = counts.setdefault(fleet_id, [0, 0])
        if status == FLEET_MEMBER_ACTIVE:
            active = int(count)
        if status == FLEET_MEMBER_PENDING:
            pending = int(count)
        counts[fleet_id] = [active, pending]
    return {fleet_id: (values[0], values[1]) for fleet_id, values in counts.items()}


def _attach_summary(db: Session, fleets: list[Fleet]) -> list[Fleet]:
    counts = _summary_counts(db)
    fleet_ids = [fleet.id for fleet in fleets]
    leader_rows = db.scalars(
        select(FleetMembership)
        .join(FleetMembership.fleet_role)
        .options(
            selectinload(FleetMembership.user),
            selectinload(FleetMembership.fleet),
            selectinload(FleetMembership.fleet_role),
        )
        .where(
            FleetMembership.fleet_id.in_(fleet_ids or [-1]),
            FleetRoleDefinition.is_leadership.is_(True),
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
        )
        .order_by(FleetRoleDefinition.rank.desc(), FleetMembership.joined_at, FleetMembership.id)
    ).all()
    leaders_by_fleet: dict[int, list[FleetMembership]] = {}
    for row in leader_rows:
        leaders_by_fleet.setdefault(row.fleet_id, []).append(row)
    for fleet in fleets:
        active, pending = counts.get(fleet.id, (0, 0))
        fleet.active_members_count = active
        fleet.pending_members_count = pending
        fleet.leaders = leaders_by_fleet.get(fleet.id, [])
    return fleets


def list_fleets(db: Session, *, include_inactive: bool = False) -> list[Fleet]:
    fleet = get_primary_fleet(db)
    if fleet is None:
        return []
    if not include_inactive and not fleet.is_active:
        return []
    return [fleet]


def get_fleet(db: Session, fleet_id: int, *, include_members: bool = False) -> Fleet | None:
    primary = get_primary_fleet(db, include_members=include_members)
    if primary is None or primary.id != fleet_id:
        return None
    return primary


def list_user_memberships(db: Session, user: User) -> list[FleetMembership]:
    return list(
        db.scalars(
            select(FleetMembership)
            .where(FleetMembership.user_id == user.id)
            .options(
                selectinload(FleetMembership.user),
                selectinload(FleetMembership.fleet),
                selectinload(FleetMembership.fleet_role),
            )
            .order_by(FleetMembership.status, FleetMembership.joined_at.desc())
        ).all()
    )


def user_leadership_memberships(db: Session, user: User) -> list[FleetMembership]:
    return list(
        db.scalars(
            select(FleetMembership)
            .join(FleetMembership.fleet_role)
            .where(
                FleetMembership.user_id == user.id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
                FleetRoleDefinition.is_leadership.is_(True),
            )
            .options(selectinload(FleetMembership.fleet), selectinload(FleetMembership.fleet_role))
            .order_by(FleetRoleDefinition.rank.desc(), FleetMembership.fleet_id)
        ).all()
    )


def can_manage_fleet(db: Session, user: User, fleet_id: int | None = None) -> bool:
    if user.can_moderate:
        return True
    primary_id = db.scalar(
        select(Fleet.id)
        .where(Fleet.is_active.is_(True))
        .order_by(
            case((Fleet.slug == PRIMARY_FLEET_SLUG, 0), else_=1),
            Fleet.sort_order,
            Fleet.id,
        )
        .limit(1)
    )
    if primary_id is None or (fleet_id is not None and fleet_id != primary_id):
        return False
    return db.scalar(
        select(FleetMembership.id)
        .join(FleetMembership.fleet_role)
        .where(
            FleetMembership.user_id == user.id,
            FleetMembership.fleet_id == primary_id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
            FleetRoleDefinition.can_manage_fleet.is_(True),
        )
    ) is not None


def create_fleet(db: Session, payload: FleetCreate) -> Fleet:
    if get_primary_fleet(db) is not None:
        raise FleetValidationError("The official fleet is already configured.")
    fleet = Fleet(**payload.model_dump())
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return get_primary_fleet(db) or fleet


def update_fleet(db: Session, fleet_id: int, payload: FleetUpdate) -> Fleet | None:
    fleet = get_fleet(db, fleet_id)
    if fleet is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] != fleet.slug and db.scalar(select(Fleet).where(Fleet.slug == data["slug"])):
        raise FleetValidationError("Fleet slug already exists.")
    if "name" in data and data["name"] != fleet.name and db.scalar(select(Fleet).where(Fleet.name == data["name"])):
        raise FleetValidationError("Fleet name already exists.")
    for field, value in data.items():
        setattr(fleet, field, value)
    db.commit()
    return get_primary_fleet(db)


def join_fleet(db: Session, user: User, payload: FleetJoinRequest) -> FleetMembership:
    fleet = get_primary_fleet(db)
    if fleet is None or not fleet.is_active:
        raise FleetValidationError("Official fleet not found.")
    if payload.fleet_id is not None and payload.fleet_id != fleet.id:
        raise FleetValidationError("Only the official fleet can be joined.")

    existing = db.scalar(select(FleetMembership).where(FleetMembership.user_id == user.id))
    if existing is None:
        existing = FleetMembership(
            fleet_id=fleet.id,
            user_id=user.id,
            status=FLEET_MEMBER_PENDING,
            note=payload.note,
        )
        assign_fleet_role_definition(db, existing, FLEET_ROLE_MEMBER)
        db.add(existing)
    else:
        existing.fleet_id = fleet.id
        existing.status = FLEET_MEMBER_PENDING if existing.status == "inactive" else existing.status
        existing.note = payload.note
    db.commit()
    db.refresh(existing)
    return existing


def update_membership(
    db: Session,
    membership_id: int,
    payload: FleetMembershipUpdate,
    *,
    actor: User,
) -> FleetMembership | None:
    membership = db.get(FleetMembership, membership_id)
    if membership is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    changed_fields = set(data)
    role = data.pop("role", None)
    if role:
        try:
            get_fleet_role(db, role)
        except ValueError as exc:
            raise FleetValidationError("Invalid or inactive fleet role.") from exc
    status = data.get("status")
    if status and status not in FLEET_MEMBER_STATUSES:
        raise FleetValidationError("Invalid membership status.")

    validate_membership_update(
        db,
        actor=actor,
        target=membership,
        changed_fields=changed_fields,
        requested_role=role,
    )

    if role:
        assign_fleet_role_definition(db, membership, role)
    for field, value in data.items():
        setattr(membership, field, value)
    db.commit()
    db.refresh(membership)
    return membership


def assign_fleet_role(db: Session, fleet_id: int | None, user_id: int, role: str = FLEET_ROLE_ADMIRAL) -> FleetMembership:
    try:
        role_definition = get_fleet_role(db, role)
    except ValueError as exc:
        raise FleetValidationError("Invalid or inactive fleet role.") from exc
    fleet = get_primary_fleet(db)
    user = db.get(User, user_id)
    if fleet is None or user is None:
        raise FleetValidationError("Fleet or user not found.")
    if fleet_id is not None and fleet_id != fleet.id:
        raise FleetValidationError("Only the official fleet can be managed.")
    membership = db.scalar(select(FleetMembership).where(FleetMembership.user_id == user_id))
    if membership is None:
        membership = FleetMembership(fleet_id=fleet.id, user_id=user_id, status=FLEET_MEMBER_ACTIVE)
        db.add(membership)
    else:
        membership.fleet_id = fleet.id
        membership.status = FLEET_MEMBER_ACTIVE
    membership.fleet_role = role_definition
    db.commit()
    db.refresh(membership)
    return membership
