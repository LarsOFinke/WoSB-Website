from __future__ import annotations

from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload

from app.models import Group, GroupParticipant


_GROUP_LOAD_OPTIONS = (
    selectinload(Group.ship),
    selectinload(Group.owner),
    selectinload(Group.participants).selectinload(GroupParticipant.ship),
)


class GroupRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, group_id: int) -> Group | None:
        stmt = select(Group).where(Group.id == group_id).options(*_GROUP_LOAD_OPTIONS)
        return self.db.scalars(stmt).first()

    def list(self, *, limit: int = 100, include_inactive: bool = False) -> list[Group]:
        stmt = select(Group).options(*_GROUP_LOAD_OPTIONS)
        if not include_inactive:
            stmt = stmt.where(Group.active.is_(True))
        stmt = (
            stmt.order_by(
                case((Group.status == "open", 0), (Group.status == "full", 1), else_=2),
                Group.expires_at.is_(None),
                Group.expires_at,
                Group.scheduled_at.is_(None),
                Group.scheduled_at,
                Group.created_at.desc(),
            )
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_by_owner(self, owner_id: int, *, limit: int = 100, include_inactive: bool = True) -> list[Group]:
        stmt = select(Group).where(Group.owner_id == owner_id).options(*_GROUP_LOAD_OPTIONS)
        if not include_inactive:
            stmt = stmt.where(Group.active.is_(True))
        stmt = (
            stmt.order_by(Group.active.desc(), Group.expires_at.is_(None), Group.expires_at, Group.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def create(self, group: Group) -> Group:
        self.db.add(group)
        self.db.flush()
        self.db.refresh(group)
        return group

    def delete(self, group: Group) -> None:
        self.db.delete(group)
        self.db.flush()

    def add_participant(self, participant: GroupParticipant) -> GroupParticipant:
        self.db.add(participant)
        self.db.flush()
        self.db.refresh(participant)
        return participant

    def get_participant_by_token_hash(self, token_hash: str) -> GroupParticipant | None:
        stmt = select(GroupParticipant).where(GroupParticipant.anonymous_edit_token_hash == token_hash)
        return self.db.scalars(stmt).first()

    def get_participant_by_token(self, join_token: str) -> GroupParticipant | None:
        # Legacy fallback for pre-hash local development data.
        stmt = select(GroupParticipant).where(GroupParticipant.join_token == join_token)
        return self.db.scalars(stmt).first()
