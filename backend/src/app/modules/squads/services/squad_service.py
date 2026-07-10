from __future__ import annotations

import re
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.fleet.models.fleet import FLEET_MEMBER_ACTIVE
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.services.fleet_service import can_manage_fleet, get_primary_fleet
from app.modules.squads.models.squad import Squad
from app.modules.squads.models.squad_member import (
    SQUAD_MANAGEMENT_ROLES,
    SQUAD_ROLE_LEADER,
    SQUAD_ROLE_MEMBER,
    SQUAD_ROLE_OFFICER,
    SquadMember,
)
from app.modules.squads.schemas.squad import (
    SquadCreate,
    SquadDetailRead,
    SquadMemberCreate,
    SquadMemberRead,
    SquadMemberUpdate,
    SquadRosterMemberRead,
    SquadSummaryRead,
    SquadUpdate,
)


class SquadValidationError(ValueError):
    pass


class SquadPermissionError(PermissionError):
    pass


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "squad"


def _unique_slug(db: Session, fleet_id: int, name: str, *, exclude_id: int | None = None) -> str:
    base = _slugify(name)
    candidate = base
    suffix = 2
    while True:
        statement = select(Squad.id).where(Squad.fleet_id == fleet_id, Squad.slug == candidate)
        if exclude_id is not None:
            statement = statement.where(Squad.id != exclude_id)
        if db.scalar(statement) is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def _squad_query():
    return select(Squad).options(
        selectinload(Squad.members)
        .selectinload(SquadMember.fleet_membership)
        .selectinload(FleetMembership.user)
    )


def get_squad_model(db: Session, squad_id: int) -> Squad | None:
    return db.scalar(_squad_query().where(Squad.id == squad_id))


def _active_fleet_membership(db: Session, user: User, fleet_id: int | None = None) -> FleetMembership | None:
    statement = select(FleetMembership).where(
        FleetMembership.user_id == user.id,
        FleetMembership.status == FLEET_MEMBER_ACTIVE,
    )
    if fleet_id is not None:
        statement = statement.where(FleetMembership.fleet_id == fleet_id)
    return db.scalar(statement)


def _user_squad_member(db: Session, user: User, squad_id: int) -> SquadMember | None:
    return db.scalar(
        select(SquadMember)
        .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
        .where(
            SquadMember.squad_id == squad_id,
            FleetMembership.user_id == user.id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
        )
    )


def user_squad_ids(db: Session, user: User) -> list[int]:
    return list(
        db.scalars(
            select(SquadMember.squad_id)
            .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
            .join(Squad, SquadMember.squad_id == Squad.id)
            .where(
                FleetMembership.user_id == user.id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
                Squad.is_active.is_(True),
            )
            .order_by(SquadMember.squad_id)
        ).all()
    )


def user_managed_squad_ids(db: Session, user: User) -> list[int]:
    if can_manage_fleet(db, user):
        return list(db.scalars(select(Squad.id).where(Squad.is_active.is_(True)).order_by(Squad.id)).all())
    return list(
        db.scalars(
            select(SquadMember.squad_id)
            .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
            .join(Squad, SquadMember.squad_id == Squad.id)
            .where(
                FleetMembership.user_id == user.id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
                SquadMember.role.in_(SQUAD_MANAGEMENT_ROLES),
                Squad.is_active.is_(True),
            )
            .order_by(SquadMember.squad_id)
        ).all()
    )


def can_manage_squad(db: Session, user: User, squad: Squad | int) -> bool:
    squad_id = squad if isinstance(squad, int) else squad.id
    fleet_id = None if isinstance(squad, int) else squad.fleet_id
    if can_manage_fleet(db, user, fleet_id):
        return True
    member = _user_squad_member(db, user, squad_id)
    return member is not None and member.role in SQUAD_MANAGEMENT_ROLES


def can_administer_squad(db: Session, user: User, squad: Squad | int) -> bool:
    """Return whether a user may change leadership and officer assignments.

    Officers are deliberately allowed to run day-to-day organization and squad
    calendar entries, but they cannot promote themselves, replace the leader or
    remove other officers. Fleet leadership and the current squad leader retain
    those structural permissions.
    """

    squad_id = squad if isinstance(squad, int) else squad.id
    fleet_id = None if isinstance(squad, int) else squad.fleet_id
    if can_manage_fleet(db, user, fleet_id):
        return True
    member = _user_squad_member(db, user, squad_id)
    return member is not None and member.role == SQUAD_ROLE_LEADER


def can_view_squad_event(db: Session, user: User, squad_id: int | None) -> bool:
    if squad_id is None or can_manage_fleet(db, user):
        return True
    return squad_id in set(user_squad_ids(db, user))


def _member_read(member: SquadMember, *, include_note: bool = True) -> SquadMemberRead:
    membership = member.fleet_membership
    return SquadMemberRead(
        id=member.id,
        fleet_membership_id=membership.id,
        user_id=membership.user_id,
        display_name=membership.user.display_name,
        fleet_role=membership.role,
        squad_role=member.role,
        note=member.note if include_note else None,
        joined_at=member.joined_at,
    )


def _summary_read(db: Session, squad: Squad, user: User) -> SquadSummaryRead:
    may_manage = can_manage_squad(db, user, squad)
    members = [_member_read(member, include_note=may_manage) for member in squad.members]
    leader = next((member for member in members if member.squad_role == SQUAD_ROLE_LEADER), None)
    active_membership = _active_fleet_membership(db, user, squad.fleet_id)
    current_member = next(
        (member for member in members if active_membership is not None and member.fleet_membership_id == active_membership.id),
        None,
    )
    return SquadSummaryRead(
        id=squad.id,
        fleet_id=squad.fleet_id,
        name=squad.name,
        slug=squad.slug,
        description=squad.description,
        focus=squad.focus,
        max_members=squad.max_members,
        is_active=squad.is_active,
        leader=leader,
        member_count=len(members),
        is_member=current_member is not None,
        current_user_role=current_member.squad_role if current_member is not None else None,
        can_manage=may_manage,
        can_administer=can_administer_squad(db, user, squad),
        created_at=squad.created_at,
        updated_at=squad.updated_at,
    )


def _detail_read(db: Session, squad: Squad, user: User) -> SquadDetailRead:
    summary = _summary_read(db, squad, user)
    may_manage = summary.can_manage
    members = sorted(
        (_member_read(member, include_note=may_manage) for member in squad.members),
        key=lambda item: (
            {SQUAD_ROLE_LEADER: 0, SQUAD_ROLE_OFFICER: 1, SQUAD_ROLE_MEMBER: 2}[item.squad_role],
            item.display_name.casefold(),
        ),
    )
    return SquadDetailRead(**summary.model_dump(), members=members)


def list_squads(db: Session, user: User, *, include_inactive: bool = False) -> list[SquadSummaryRead]:
    statement = _squad_query()
    if not include_inactive or not can_manage_fleet(db, user):
        statement = statement.where(Squad.is_active.is_(True))
    statement = statement.order_by(Squad.name.asc(), Squad.id.asc())
    return [_summary_read(db, squad, user) for squad in db.scalars(statement).unique().all()]


def list_my_squads(db: Session, user: User) -> list[SquadSummaryRead]:
    """Return active squads the current user is assigned to.

    Fleet or site administration rights do not implicitly create a squad
    membership. The personal workspace therefore only contains explicit,
    active assignments from the official fleet roster.
    """

    statement = (
        _squad_query()
        .join(SquadMember, SquadMember.squad_id == Squad.id)
        .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
        .where(
            FleetMembership.user_id == user.id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
            Squad.is_active.is_(True),
        )
        .order_by(Squad.name.asc(), Squad.id.asc())
    )
    return [_summary_read(db, squad, user) for squad in db.scalars(statement).unique().all()]


def get_squad(db: Session, squad_id: int, user: User) -> SquadDetailRead | None:
    squad = get_squad_model(db, squad_id)
    if squad is None:
        return None
    if not squad.is_active and not can_manage_squad(db, user, squad):
        return None
    return _detail_read(db, squad, user)


def _validate_active_membership(db: Session, fleet_id: int, membership_id: int) -> FleetMembership:
    membership = db.scalar(
        select(FleetMembership)
        .options(selectinload(FleetMembership.user))
        .where(
            FleetMembership.id == membership_id,
            FleetMembership.fleet_id == fleet_id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
        )
    )
    if membership is None:
        raise SquadValidationError("The selected player is not an active member of this fleet.")
    return membership


def create_squad(db: Session, payload: SquadCreate, user: User) -> SquadDetailRead:
    fleet = get_primary_fleet(db)
    if fleet is None:
        raise SquadValidationError("Official fleet not found.")
    if not can_manage_fleet(db, user, fleet.id):
        raise SquadPermissionError("Fleet leadership access required to create squads.")
    if db.scalar(
        select(Squad.id).where(Squad.fleet_id == fleet.id, func.lower(Squad.name) == payload.name.casefold())
    ) is not None:
        raise SquadValidationError("A squad with this name already exists.")
    leader = _validate_active_membership(db, fleet.id, payload.leader_membership_id)
    squad = Squad(
        fleet_id=fleet.id,
        name=payload.name,
        slug=_unique_slug(db, fleet.id, payload.name),
        description=payload.description,
        focus=payload.focus,
        max_members=payload.max_members,
        created_by_id=user.id,
    )
    db.add(squad)
    db.flush()
    db.add(SquadMember(squad_id=squad.id, fleet_membership_id=leader.id, role=SQUAD_ROLE_LEADER))
    db.commit()
    created = get_squad_model(db, squad.id)
    if created is None:
        raise SquadValidationError("Squad could not be loaded after creation.")
    return _detail_read(db, created, user)


def update_squad(db: Session, squad_id: int, payload: SquadUpdate, user: User) -> SquadDetailRead | None:
    squad = get_squad_model(db, squad_id)
    if squad is None:
        return None
    if not can_manage_squad(db, user, squad):
        raise SquadPermissionError("Squad leadership access required.")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != squad.name:
        if db.scalar(
            select(Squad.id).where(
                Squad.fleet_id == squad.fleet_id,
                Squad.id != squad.id,
                func.lower(Squad.name) == data["name"].casefold(),
            )
        ) is not None:
            raise SquadValidationError("A squad with this name already exists.")
        squad.slug = _unique_slug(db, squad.fleet_id, data["name"], exclude_id=squad.id)
    for field, value in data.items():
        setattr(squad, field, value)
    if squad.max_members is not None and len(squad.members) > squad.max_members:
        raise SquadValidationError("Maximum squad size cannot be lower than the current member count.")
    db.commit()
    updated = get_squad_model(db, squad.id)
    return _detail_read(db, updated, user) if updated is not None else None


def archive_squad(db: Session, squad_id: int, user: User) -> bool:
    squad = get_squad_model(db, squad_id)
    if squad is None:
        return False
    if not can_manage_fleet(db, user, squad.fleet_id):
        raise SquadPermissionError("Fleet leadership access required to archive squads.")
    squad.is_active = False
    db.commit()
    return True


def _transfer_leadership(squad: Squad, new_leader_id: int) -> None:
    for member in squad.members:
        if member.id == new_leader_id:
            member.role = SQUAD_ROLE_LEADER
        elif member.role == SQUAD_ROLE_LEADER:
            member.role = SQUAD_ROLE_OFFICER


def add_squad_member(
    db: Session,
    squad_id: int,
    payload: SquadMemberCreate,
    user: User,
) -> SquadDetailRead | None:
    squad = get_squad_model(db, squad_id)
    if squad is None or not squad.is_active:
        return None
    if not can_manage_squad(db, user, squad):
        raise SquadPermissionError("Squad leadership access required.")
    if payload.role != SQUAD_ROLE_MEMBER and not can_administer_squad(db, user, squad):
        raise SquadPermissionError("Only squad or fleet leadership can assign command roles.")
    membership = _validate_active_membership(db, squad.fleet_id, payload.fleet_membership_id)
    existing = next((row for row in squad.members if row.fleet_membership_id == membership.id), None)
    if existing is None:
        if squad.max_members is not None and len(squad.members) >= squad.max_members:
            raise SquadValidationError("This squad has reached its configured member limit.")
        existing = SquadMember(
            squad_id=squad.id,
            fleet_membership_id=membership.id,
            role=payload.role,
            note=payload.note,
        )
        db.add(existing)
        db.flush()
        squad.members.append(existing)
    else:
        existing.role = payload.role
        existing.note = payload.note
    if payload.role == SQUAD_ROLE_LEADER:
        _transfer_leadership(squad, existing.id)
    db.commit()
    updated = get_squad_model(db, squad.id)
    return _detail_read(db, updated, user) if updated is not None else None


def update_squad_member(
    db: Session,
    squad_id: int,
    member_id: int,
    payload: SquadMemberUpdate,
    user: User,
) -> SquadDetailRead | None:
    squad = get_squad_model(db, squad_id)
    if squad is None:
        return None
    if not can_manage_squad(db, user, squad):
        raise SquadPermissionError("Squad leadership access required.")
    member = next((row for row in squad.members if row.id == member_id), None)
    if member is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    requested_role = data.get("role")
    if requested_role is not None and requested_role != member.role and not can_administer_squad(db, user, squad):
        raise SquadPermissionError("Only squad or fleet leadership can change command roles.")
    if data.get("role") == SQUAD_ROLE_LEADER:
        _transfer_leadership(squad, member.id)
        data.pop("role", None)
    elif member.role == SQUAD_ROLE_LEADER and data.get("role") in {SQUAD_ROLE_MEMBER, SQUAD_ROLE_OFFICER}:
        raise SquadValidationError("Transfer squad leadership before demoting the current leader.")
    for field, value in data.items():
        setattr(member, field, value)
    db.commit()
    updated = get_squad_model(db, squad.id)
    return _detail_read(db, updated, user) if updated is not None else None


def remove_squad_member(db: Session, squad_id: int, member_id: int, user: User) -> SquadDetailRead | None:
    squad = get_squad_model(db, squad_id)
    if squad is None:
        return None
    if not can_manage_squad(db, user, squad):
        raise SquadPermissionError("Squad leadership access required.")
    member = next((row for row in squad.members if row.id == member_id), None)
    if member is None:
        return None
    if member.role == SQUAD_ROLE_LEADER:
        raise SquadValidationError("Transfer squad leadership before removing the current leader.")
    if member.role == SQUAD_ROLE_OFFICER and not can_administer_squad(db, user, squad):
        raise SquadPermissionError("Only squad or fleet leadership can remove squad officers.")
    db.delete(member)
    db.commit()
    updated = get_squad_model(db, squad.id)
    return _detail_read(db, updated, user) if updated is not None else None


def list_squad_roster(db: Session, user: User) -> list[SquadRosterMemberRead]:
    primary = get_primary_fleet(db)
    if primary is None:
        return []
    if not can_manage_fleet(db, user, primary.id) and not user_managed_squad_ids(db, user):
        raise SquadPermissionError("Squad leadership access required.")
    memberships = list(
        db.scalars(
            select(FleetMembership)
            .options(selectinload(FleetMembership.user))
            .where(
                FleetMembership.fleet_id == primary.id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
            )
            .order_by(FleetMembership.user_id)
        ).all()
    )
    squad_rows = db.execute(
        select(SquadMember.fleet_membership_id, SquadMember.squad_id).join(Squad).where(Squad.is_active.is_(True))
    ).all()
    squad_ids_by_membership: dict[int, list[int]] = {}
    for membership_id, squad_id in squad_rows:
        squad_ids_by_membership.setdefault(membership_id, []).append(squad_id)
    return [
        SquadRosterMemberRead(
            fleet_membership_id=membership.id,
            user_id=membership.user_id,
            display_name=membership.user.display_name,
            fleet_role=membership.role,
            squad_ids=sorted(squad_ids_by_membership.get(membership.id, [])),
        )
        for membership in sorted(memberships, key=lambda row: row.user.display_name.casefold())
    ]
