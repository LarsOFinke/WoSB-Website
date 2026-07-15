from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.fleet.services.fleet_service import can_manage_fleet
from app.modules.squads.models.squad import Squad
from app.modules.squads.models.squad_member import (
    SQUAD_MANAGEMENT_ROLES,
    SQUAD_ROLE_LEADER,
)

from .repository import SquadRepository


class SquadAccessPolicy:
    def __init__(self, db: Session, repository: SquadRepository | None = None) -> None:
        self.db = db
        self.repository = repository or SquadRepository(db)

    def can_manage(self, user: User, squad: Squad | int) -> bool:
        squad_id, fleet_id = self._identifiers(squad)
        if can_manage_fleet(self.db, user, fleet_id):
            return True
        member = self.repository.user_member(user, squad_id)
        return member is not None and member.role in SQUAD_MANAGEMENT_ROLES

    def can_administer(self, user: User, squad: Squad | int) -> bool:
        squad_id, fleet_id = self._identifiers(squad)
        if can_manage_fleet(self.db, user, fleet_id):
            return True
        member = self.repository.user_member(user, squad_id)
        return member is not None and member.role == SQUAD_ROLE_LEADER

    def can_view_event(self, user: User, squad_id: int | None) -> bool:
        if squad_id is None or can_manage_fleet(self.db, user):
            return True
        return squad_id in set(self.repository.user_squad_ids(user))

    def managed_squad_ids(self, user: User) -> list[int]:
        if can_manage_fleet(self.db, user):
            return list(
                self.db.scalars(
                    select(Squad.id).where(Squad.is_active.is_(True)).order_by(Squad.id)
                ).all()
            )
        return self.repository.managed_squad_ids(user)

    @staticmethod
    def _identifiers(squad: Squad | int) -> tuple[int, int | None]:
        return (
            (squad, None)
            if isinstance(squad, int)
            else (squad.id, squad.fleet_id)
        )
