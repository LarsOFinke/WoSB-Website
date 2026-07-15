from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.fleet.models.fleet import FLEET_MEMBER_ACTIVE
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.services.fleet_service import can_manage_fleet, get_primary_fleet
from app.modules.permissions.services.role_service import assign_squad_role
from app.modules.squads.models.squad import Squad
from app.modules.squads.models.squad_member import (
    SQUAD_ROLE_LEADER,
    SQUAD_ROLE_MEMBER,
    SQUAD_ROLE_OFFICER,
    SquadMember,
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

from .errors import SquadPermissionError, SquadValidationError
from .mapper import SquadMapper
from .policy import SquadAccessPolicy
from .repository import SquadRepository


class SquadService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SquadRepository(db)
        self.policy = SquadAccessPolicy(db, self.repository)
        self.mapper = SquadMapper(db, self.repository, self.policy)

    def list(self, user: User, *, include_inactive: bool = False) -> list[SquadSummaryRead]:
        statement = self.repository.query()
        if not include_inactive or not can_manage_fleet(self.db, user):
            statement = statement.where(Squad.is_active.is_(True))
        statement = statement.order_by(Squad.name.asc(), Squad.id.asc())
        return [
            self.mapper.summary(squad, user)
            for squad in self.db.scalars(statement).unique().all()
        ]

    def list_mine(self, user: User) -> list[SquadSummaryRead]:
        statement = (
            self.repository.query()
            .join(SquadMember, SquadMember.squad_id == Squad.id)
            .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
            .where(
                FleetMembership.user_id == user.id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
                Squad.is_active.is_(True),
            )
            .order_by(Squad.name.asc(), Squad.id.asc())
        )
        return [
            self.mapper.summary(squad, user)
            for squad in self.db.scalars(statement).unique().all()
        ]

    def get(self, squad_id: int, user: User) -> SquadDetailRead | None:
        squad = self.repository.get(squad_id)
        if squad is None or (not squad.is_active and not self.policy.can_manage(user, squad)):
            return None
        return self.mapper.detail(squad, user)

    def create(self, payload: SquadCreate, user: User) -> SquadDetailRead:
        fleet = get_primary_fleet(self.db)
        if fleet is None:
            raise SquadValidationError("Official fleet not found.")
        if not can_manage_fleet(self.db, user, fleet.id):
            raise SquadPermissionError("Fleet leadership access required to create squads.")
        self._ensure_unique_name(fleet.id, payload.name)
        leader = self.repository.required_active_membership(
            fleet.id, payload.leader_membership_id
        )
        squad = Squad(
            fleet_id=fleet.id,
            name=payload.name,
            slug=self.repository.unique_slug(fleet.id, payload.name),
            description=payload.description,
            focus=payload.focus,
            max_members=payload.max_members,
            created_by_id=user.id,
        )
        self.db.add(squad)
        self.db.flush()
        leader_member = SquadMember(squad_id=squad.id, fleet_membership_id=leader.id)
        assign_squad_role(self.db, leader_member, SQUAD_ROLE_LEADER)
        self.db.add(leader_member)
        self.db.commit()
        return self.mapper.detail(self._required_reloaded(squad.id), user)

    def update(
        self, squad_id: int, payload: SquadUpdate, user: User
    ) -> SquadDetailRead | None:
        squad = self.repository.get(squad_id)
        if squad is None:
            return None
        if not self.policy.can_manage(user, squad):
            raise SquadPermissionError("Squad leadership access required.")
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] != squad.name:
            self._ensure_unique_name(squad.fleet_id, data["name"], exclude_id=squad.id)
            squad.slug = self.repository.unique_slug(
                squad.fleet_id, data["name"], exclude_id=squad.id
            )
        for field, value in data.items():
            setattr(squad, field, value)
        if squad.max_members is not None and len(squad.members) > squad.max_members:
            raise SquadValidationError(
                "Maximum squad size cannot be lower than the current member count."
            )
        self.db.commit()
        updated = self.repository.get(squad.id)
        return self.mapper.detail(updated, user) if updated is not None else None

    def archive(self, squad_id: int, user: User) -> bool:
        squad = self.repository.get(squad_id)
        if squad is None:
            return False
        if not can_manage_fleet(self.db, user, squad.fleet_id):
            raise SquadPermissionError("Fleet leadership access required to archive squads.")
        squad.is_active = False
        self.db.commit()
        return True

    def add_member(
        self, squad_id: int, payload: SquadMemberCreate, user: User
    ) -> SquadDetailRead | None:
        squad = self.repository.get(squad_id)
        if squad is None or not squad.is_active:
            return None
        self._require_manage(user, squad)
        if payload.role != SQUAD_ROLE_MEMBER and not self.policy.can_administer(user, squad):
            raise SquadPermissionError(
                "Only squad or fleet leadership can assign command roles."
            )
        membership = self.repository.required_active_membership(
            squad.fleet_id, payload.fleet_membership_id
        )
        member = next(
            (row for row in squad.members if row.fleet_membership_id == membership.id),
            None,
        )
        if member is None:
            if squad.max_members is not None and len(squad.members) >= squad.max_members:
                raise SquadValidationError(
                    "This squad has reached its configured member limit."
                )
            member = SquadMember(
                squad_id=squad.id,
                fleet_membership_id=membership.id,
                note=payload.note,
            )
            assign_squad_role(self.db, member, payload.role)
            self.db.add(member)
            self.db.flush()
            squad.members.append(member)
        else:
            assign_squad_role(self.db, member, payload.role)
            member.note = payload.note
        if payload.role == SQUAD_ROLE_LEADER:
            self._transfer_leadership(squad, member.id)
        return self._commit_and_detail(squad.id, user)

    def update_member(
        self,
        squad_id: int,
        member_id: int,
        payload: SquadMemberUpdate,
        user: User,
    ) -> SquadDetailRead | None:
        squad = self.repository.get(squad_id)
        if squad is None:
            return None
        self._require_manage(user, squad)
        member = next((row for row in squad.members if row.id == member_id), None)
        if member is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        requested_role = data.get("role")
        if (
            requested_role is not None
            and requested_role != member.role
            and not self.policy.can_administer(user, squad)
        ):
            raise SquadPermissionError(
                "Only squad or fleet leadership can change command roles."
            )
        if requested_role == SQUAD_ROLE_LEADER:
            self._transfer_leadership(squad, member.id)
            data.pop("role", None)
        elif member.role == SQUAD_ROLE_LEADER and requested_role in {
            SQUAD_ROLE_MEMBER,
            SQUAD_ROLE_OFFICER,
        }:
            raise SquadValidationError(
                "Transfer squad leadership before demoting the current leader."
            )
        role = data.pop("role", None)
        if role is not None:
            assign_squad_role(self.db, member, role)
        for field, value in data.items():
            setattr(member, field, value)
        return self._commit_and_detail(squad.id, user)

    def remove_member(
        self, squad_id: int, member_id: int, user: User
    ) -> SquadDetailRead | None:
        squad = self.repository.get(squad_id)
        if squad is None:
            return None
        self._require_manage(user, squad)
        member = next((row for row in squad.members if row.id == member_id), None)
        if member is None:
            return None
        if member.role == SQUAD_ROLE_LEADER:
            raise SquadValidationError(
                "Transfer squad leadership before removing the current leader."
            )
        if member.role == SQUAD_ROLE_OFFICER and not self.policy.can_administer(user, squad):
            raise SquadPermissionError(
                "Only squad or fleet leadership can remove squad officers."
            )
        self.db.delete(member)
        return self._commit_and_detail(squad.id, user)

    def roster(self, user: User) -> list[SquadRosterMemberRead]:
        primary = get_primary_fleet(self.db)
        if primary is None:
            return []
        if not can_manage_fleet(self.db, user, primary.id) and not self.policy.managed_squad_ids(user):
            raise SquadPermissionError("Squad leadership access required.")
        memberships = list(
            self.db.scalars(
                select(FleetMembership)
                .options(selectinload(FleetMembership.user))
                .where(
                    FleetMembership.fleet_id == primary.id,
                    FleetMembership.status == FLEET_MEMBER_ACTIVE,
                )
                .order_by(FleetMembership.user_id)
            ).all()
        )
        rows = self.db.execute(
            select(SquadMember.fleet_membership_id, SquadMember.squad_id)
            .join(Squad)
            .where(Squad.is_active.is_(True))
        ).all()
        squad_ids: dict[int, list[int]] = {}
        for membership_id, squad_id in rows:
            squad_ids.setdefault(membership_id, []).append(squad_id)
        return [
            SquadRosterMemberRead(
                fleet_membership_id=membership.id,
                user_id=membership.user_id,
                display_name=membership.user.display_name,
                fleet_role=membership.role,
                squad_ids=sorted(squad_ids.get(membership.id, [])),
            )
            for membership in sorted(
                memberships, key=lambda row: row.user.display_name.casefold()
            )
        ]

    def _ensure_unique_name(
        self, fleet_id: int, name: str, *, exclude_id: int | None = None
    ) -> None:
        statement = select(Squad.id).where(
            Squad.fleet_id == fleet_id,
            func.lower(Squad.name) == name.casefold(),
        )
        if exclude_id is not None:
            statement = statement.where(Squad.id != exclude_id)
        if self.db.scalar(statement) is not None:
            raise SquadValidationError("A squad with this name already exists.")

    def _require_manage(self, user: User, squad: Squad) -> None:
        if not self.policy.can_manage(user, squad):
            raise SquadPermissionError("Squad leadership access required.")

    def _transfer_leadership(self, squad: Squad, new_leader_id: int) -> None:
        for member in squad.members:
            if member.id == new_leader_id:
                assign_squad_role(self.db, member, SQUAD_ROLE_LEADER)
            elif member.role == SQUAD_ROLE_LEADER:
                assign_squad_role(self.db, member, SQUAD_ROLE_OFFICER)

    def _commit_and_detail(self, squad_id: int, user: User) -> SquadDetailRead | None:
        self.db.commit()
        updated = self.repository.get(squad_id)
        return self.mapper.detail(updated, user) if updated is not None else None

    def _required_reloaded(self, squad_id: int) -> Squad:
        squad = self.repository.get(squad_id)
        if squad is None:
            raise SquadValidationError("Squad could not be loaded after creation.")
        return squad
