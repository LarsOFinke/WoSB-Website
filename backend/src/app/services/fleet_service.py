from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Fleet, FleetMembership, User
from app.models.fleet import (
    FLEET_LEADERSHIP_ROLES,
    FLEET_MEMBER_ACTIVE,
    FLEET_MEMBER_PENDING,
    FLEET_ROLE_ADMIRAL,
    FLEET_ROLE_MEMBER,
    FLEET_ROLES,
    FLEET_MEMBER_STATUSES,
)
from app.schemas.fleet import FleetCreate, FleetJoinRequest, FleetMembershipUpdate, FleetUpdate


class FleetValidationError(ValueError):
    pass


def _membership_priority(membership: FleetMembership) -> tuple[int, int, int]:
    """Sort active memberships before pending ones, newest first within status."""

    status_rank = 0 if membership.status == FLEET_MEMBER_ACTIVE else 1 if membership.status == FLEET_MEMBER_PENDING else 2
    timestamp = membership.updated_at or membership.joined_at
    return (status_rank, -int(timestamp.timestamp()), -membership.id)


def _select_profile_membership(memberships: list[FleetMembership]) -> FleetMembership | None:
    candidates = [row for row in memberships if row.status in {FLEET_MEMBER_ACTIVE, FLEET_MEMBER_PENDING}]
    return sorted(candidates, key=_membership_priority)[0] if candidates else None


def sync_user_primary_fleet(
    db: Session,
    user: User,
    *,
    preferred_membership: FleetMembership | None = None,
    force_preferred: bool = False,
) -> User:
    """Keep the single profile fleet pointer aligned with official memberships.

    ``user_profiles.primary_fleet_membership_id`` is the canonical profile-level
    fleet value. It intentionally points to a membership row instead of copying a
    fleet name or fleet id, so role/status/fleet data cannot drift apart.
    """

    profile = user._ensure_profile()
    current = profile.primary_fleet_membership

    if (
        current is not None
        and current.user_id == user.id
        and current.status in {FLEET_MEMBER_ACTIVE, FLEET_MEMBER_PENDING}
        and not force_preferred
    ):
        return user

    target = None
    if (
        preferred_membership is not None
        and preferred_membership.user_id == user.id
        and preferred_membership.status in {FLEET_MEMBER_ACTIVE, FLEET_MEMBER_PENDING}
    ):
        target = preferred_membership

    if target is None:
        memberships = list(db.scalars(
            select(FleetMembership)
            .where(FleetMembership.user_id == user.id)
            .options(selectinload(FleetMembership.fleet))
        ).all())
        target = _select_profile_membership(memberships)

    profile.primary_fleet_membership_id = target.id if target is not None else None
    db.add(profile)
    db.flush()
    return user


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
    leader_rows = db.scalars(
        select(FleetMembership)
        .options(selectinload(FleetMembership.user), selectinload(FleetMembership.fleet))
        .where(FleetMembership.role.in_(FLEET_LEADERSHIP_ROLES), FleetMembership.status == FLEET_MEMBER_ACTIVE)
        .order_by(FleetMembership.role, FleetMembership.joined_at)
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
    query = select(Fleet).order_by(Fleet.sort_order, Fleet.name)
    if not include_inactive:
        query = query.where(Fleet.is_active.is_(True))
    return _attach_summary(db, list(db.scalars(query).all()))


def get_fleet(db: Session, fleet_id: int, *, include_members: bool = False) -> Fleet | None:
    query = select(Fleet).where(Fleet.id == fleet_id)
    if include_members:
        query = query.options(selectinload(Fleet.memberships).selectinload(FleetMembership.user))
    fleet = db.scalar(query)
    if fleet is None:
        return None
    _attach_summary(db, [fleet])
    if include_members:
        fleet.memberships = sorted(fleet.memberships, key=lambda item: (item.status != FLEET_MEMBER_PENDING, item.user.display_name.casefold()))
    return fleet


def list_user_memberships(db: Session, user: User) -> list[FleetMembership]:
    memberships = list(db.scalars(
        select(FleetMembership)
        .where(FleetMembership.user_id == user.id)
        .options(selectinload(FleetMembership.user), selectinload(FleetMembership.fleet))
        .order_by(FleetMembership.status, FleetMembership.joined_at.desc())
    ).all())
    sync_user_primary_fleet(db, user)
    return memberships


def user_leadership_memberships(db: Session, user: User) -> list[FleetMembership]:
    return list(db.scalars(
        select(FleetMembership)
        .where(
            FleetMembership.user_id == user.id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
            FleetMembership.role.in_(FLEET_LEADERSHIP_ROLES),
        )
        .options(selectinload(FleetMembership.fleet))
        .order_by(FleetMembership.fleet_id)
    ).all())


def can_manage_fleet(db: Session, user: User, fleet_id: int) -> bool:
    if user.is_admin:
        return True
    return db.scalar(
        select(FleetMembership.id).where(
            FleetMembership.user_id == user.id,
            FleetMembership.fleet_id == fleet_id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
            FleetMembership.role.in_(FLEET_LEADERSHIP_ROLES),
        )
    ) is not None


def create_fleet(db: Session, payload: FleetCreate) -> Fleet:
    if db.scalar(select(Fleet).where(Fleet.slug == payload.slug)) is not None:
        raise FleetValidationError("Fleet slug already exists.")
    if db.scalar(select(Fleet).where(Fleet.name == payload.name)) is not None:
        raise FleetValidationError("Fleet name already exists.")
    fleet = Fleet(**payload.model_dump())
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return get_fleet(db, fleet.id) or fleet


def update_fleet(db: Session, fleet_id: int, payload: FleetUpdate) -> Fleet | None:
    fleet = db.get(Fleet, fleet_id)
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
    return get_fleet(db, fleet.id)


def join_fleet(db: Session, user: User, payload: FleetJoinRequest) -> FleetMembership:
    fleet = db.get(Fleet, payload.fleet_id)
    if fleet is None or not fleet.is_active:
        raise FleetValidationError("Fleet not found.")
    existing = db.scalar(select(FleetMembership).where(FleetMembership.user_id == user.id, FleetMembership.fleet_id == fleet.id))
    if existing is not None:
        existing.status = FLEET_MEMBER_PENDING if existing.status == "inactive" else existing.status
        existing.note = payload.note
        db.flush()
        sync_user_primary_fleet(db, user, preferred_membership=existing)
        db.commit()
        db.refresh(existing)
        return existing
    membership = FleetMembership(fleet_id=fleet.id, user_id=user.id, role=FLEET_ROLE_MEMBER, status=FLEET_MEMBER_PENDING, note=payload.note)
    db.add(membership)
    db.flush()
    sync_user_primary_fleet(db, user, preferred_membership=membership)
    db.commit()
    db.refresh(membership)
    return membership


def update_membership(db: Session, membership_id: int, payload: FleetMembershipUpdate) -> FleetMembership | None:
    membership = db.get(FleetMembership, membership_id)
    if membership is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    role = data.get("role")
    status = data.get("status")
    if role and role not in FLEET_ROLES:
        raise FleetValidationError("Invalid fleet role.")
    if status and status not in FLEET_MEMBER_STATUSES:
        raise FleetValidationError("Invalid membership status.")
    for field, value in data.items():
        setattr(membership, field, value)
    db.flush()
    force_preferred = membership.status == FLEET_MEMBER_ACTIVE
    sync_user_primary_fleet(db, membership.user, preferred_membership=membership, force_preferred=force_preferred)
    if membership.status == "inactive" and membership.user.profile and membership.user.profile.primary_fleet_membership_id == membership.id:
        membership.user.profile.primary_fleet_membership_id = None
        db.flush()
        sync_user_primary_fleet(db, membership.user)
    db.commit()
    db.refresh(membership)
    return membership


def assign_fleet_role(db: Session, fleet_id: int, user_id: int, role: str = FLEET_ROLE_ADMIRAL) -> FleetMembership:
    if role not in FLEET_ROLES:
        raise FleetValidationError("Invalid fleet role.")
    fleet = db.get(Fleet, fleet_id)
    user = db.get(User, user_id)
    if fleet is None or user is None:
        raise FleetValidationError("Fleet or user not found.")
    membership = db.scalar(select(FleetMembership).where(FleetMembership.fleet_id == fleet_id, FleetMembership.user_id == user_id))
    if membership is None:
        membership = FleetMembership(fleet_id=fleet_id, user_id=user_id, role=role, status=FLEET_MEMBER_ACTIVE)
        db.add(membership)
    else:
        membership.role = role
        membership.status = FLEET_MEMBER_ACTIVE
    db.flush()
    sync_user_primary_fleet(db, user, preferred_membership=membership, force_preferred=True)
    db.commit()
    db.refresh(membership)
    return membership
