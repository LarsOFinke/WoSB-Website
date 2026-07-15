from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.squads.models.squad import Squad
from app.modules.squads.models.squad_member import (
    SQUAD_ROLE_LEADER,
    SQUAD_ROLE_MEMBER,
    SQUAD_ROLE_OFFICER,
    SquadMember,
)
from app.modules.squads.schemas.squad import (
    SquadDetailRead,
    SquadMemberRead,
    SquadSummaryRead,
)

from .policy import SquadAccessPolicy
from .repository import SquadRepository


class SquadMapper:
    ROLE_ORDER = {
        SQUAD_ROLE_LEADER: 0,
        SQUAD_ROLE_OFFICER: 1,
        SQUAD_ROLE_MEMBER: 2,
    }

    def __init__(
        self,
        db: Session,
        repository: SquadRepository,
        policy: SquadAccessPolicy,
    ) -> None:
        self.db = db
        self.repository = repository
        self.policy = policy

    @staticmethod
    def member(member: SquadMember, *, include_note: bool = True) -> SquadMemberRead:
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

    def summary(self, squad: Squad, user: User) -> SquadSummaryRead:
        may_manage = self.policy.can_manage(user, squad)
        members = [self.member(member, include_note=may_manage) for member in squad.members]
        leader = next(
            (member for member in members if member.squad_role == SQUAD_ROLE_LEADER),
            None,
        )
        active_membership = self.repository.active_membership(user, squad.fleet_id)
        current_member = next(
            (
                member
                for member in members
                if active_membership is not None
                and member.fleet_membership_id == active_membership.id
            ),
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
            current_user_role=(current_member.squad_role if current_member else None),
            can_manage=may_manage,
            can_administer=self.policy.can_administer(user, squad),
            created_at=squad.created_at,
            updated_at=squad.updated_at,
        )

    def detail(self, squad: Squad, user: User) -> SquadDetailRead:
        summary = self.summary(squad, user)
        members = sorted(
            (
                self.member(member, include_note=summary.can_manage)
                for member in squad.members
            ),
            key=lambda item: (
                self.ROLE_ORDER[item.squad_role],
                item.display_name.casefold(),
            ),
        )
        return SquadDetailRead(**summary.model_dump(), members=members)
