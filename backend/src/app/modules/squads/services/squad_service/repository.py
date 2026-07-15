from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.fleet.models.fleet import FLEET_MEMBER_ACTIVE
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.permissions.models.role import SquadRoleDefinition
from app.modules.squads.models.squad import Squad
from app.modules.squads.models.squad_member import SQUAD_MANAGEMENT_ROLES, SquadMember

from .errors import SquadValidationError


class SquadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def query():
        return select(Squad).options(
            selectinload(Squad.members)
            .selectinload(SquadMember.fleet_membership)
            .selectinload(FleetMembership.user),
            selectinload(Squad.members).selectinload(SquadMember.squad_role),
            selectinload(Squad.members)
            .selectinload(SquadMember.fleet_membership)
            .selectinload(FleetMembership.fleet_role),
        )

    def get(self, squad_id: int) -> Squad | None:
        return self.db.scalar(self.query().where(Squad.id == squad_id))

    def active_membership(
        self, user: User, fleet_id: int | None = None
    ) -> FleetMembership | None:
        statement = select(FleetMembership).where(
            FleetMembership.user_id == user.id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
        )
        if fleet_id is not None:
            statement = statement.where(FleetMembership.fleet_id == fleet_id)
        return self.db.scalar(statement)

    def required_active_membership(self, fleet_id: int, membership_id: int) -> FleetMembership:
        membership = self.db.scalar(
            select(FleetMembership)
            .options(selectinload(FleetMembership.user))
            .where(
                FleetMembership.id == membership_id,
                FleetMembership.fleet_id == fleet_id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
            )
        )
        if membership is None:
            raise SquadValidationError(
                "The selected player is not an active member of this fleet."
            )
        return membership

    def user_member(self, user: User, squad_id: int) -> SquadMember | None:
        return self.db.scalar(
            select(SquadMember)
            .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
            .where(
                SquadMember.squad_id == squad_id,
                FleetMembership.user_id == user.id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
            )
        )

    def user_squad_ids(self, user: User) -> list[int]:
        return list(
            self.db.scalars(
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

    def managed_squad_ids(self, user: User) -> list[int]:
        return list(
            self.db.scalars(
                select(SquadMember.squad_id)
                .join(FleetMembership, SquadMember.fleet_membership_id == FleetMembership.id)
                .join(Squad, SquadMember.squad_id == Squad.id)
                .join(SquadMember.squad_role)
                .where(
                    FleetMembership.user_id == user.id,
                    FleetMembership.status == FLEET_MEMBER_ACTIVE,
                    SquadRoleDefinition.code.in_(SQUAD_MANAGEMENT_ROLES),
                    Squad.is_active.is_(True),
                )
                .order_by(SquadMember.squad_id)
            ).all()
        )

    def unique_slug(self, fleet_id: int, name: str, *, exclude_id: int | None = None) -> str:
        base = self.slugify(name)
        candidate = base
        suffix = 2
        while True:
            statement = select(Squad.id).where(
                Squad.fleet_id == fleet_id, Squad.slug == candidate
            )
            if exclude_id is not None:
                statement = statement.where(Squad.id != exclude_id)
            if self.db.scalar(statement) is None:
                return candidate
            candidate = f"{base}-{suffix}"
            suffix += 1

    @staticmethod
    def slugify(value: str) -> str:
        normalized = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "squad"
