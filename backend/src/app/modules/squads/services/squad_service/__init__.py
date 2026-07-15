from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.squads.models.squad import Squad
from app.modules.squads.schemas.squad import (
    SquadCreate,
    SquadMemberCreate,
    SquadMemberUpdate,
    SquadUpdate,
)

from .errors import SquadPermissionError, SquadValidationError
from .service import SquadService


def get_squad_model(db: Session, squad_id: int):
    return SquadService(db).repository.get(squad_id)


def user_squad_ids(db: Session, user: User) -> list[int]:
    return SquadService(db).repository.user_squad_ids(user)


def user_managed_squad_ids(db: Session, user: User) -> list[int]:
    return SquadService(db).policy.managed_squad_ids(user)


def can_manage_squad(db: Session, user: User, squad: Squad | int) -> bool:
    return SquadService(db).policy.can_manage(user, squad)


def can_administer_squad(db: Session, user: User, squad: Squad | int) -> bool:
    return SquadService(db).policy.can_administer(user, squad)


def can_view_squad_event(db: Session, user: User, squad_id: int | None) -> bool:
    return SquadService(db).policy.can_view_event(user, squad_id)


def list_squads(db: Session, user: User, *, include_inactive: bool = False):
    return SquadService(db).list(user, include_inactive=include_inactive)


def list_my_squads(db: Session, user: User):
    return SquadService(db).list_mine(user)


def get_squad(db: Session, squad_id: int, user: User):
    return SquadService(db).get(squad_id, user)


def create_squad(db: Session, payload: SquadCreate, user: User):
    return SquadService(db).create(payload, user)


def update_squad(db: Session, squad_id: int, payload: SquadUpdate, user: User):
    return SquadService(db).update(squad_id, payload, user)


def archive_squad(db: Session, squad_id: int, user: User) -> bool:
    return SquadService(db).archive(squad_id, user)


def add_squad_member(db: Session, squad_id: int, payload: SquadMemberCreate, user: User):
    return SquadService(db).add_member(squad_id, payload, user)


def update_squad_member(
    db: Session, squad_id: int, member_id: int, payload: SquadMemberUpdate, user: User
):
    return SquadService(db).update_member(squad_id, member_id, payload, user)


def remove_squad_member(db: Session, squad_id: int, member_id: int, user: User):
    return SquadService(db).remove_member(squad_id, member_id, user)


def list_squad_roster(db: Session, user: User):
    return SquadService(db).roster(user)


__all__ = [
    "SquadPermissionError",
    "SquadService",
    "SquadValidationError",
    "add_squad_member",
    "archive_squad",
    "can_administer_squad",
    "can_manage_squad",
    "can_view_squad_event",
    "create_squad",
    "get_squad",
    "get_squad_model",
    "list_my_squads",
    "list_squad_roster",
    "list_squads",
    "remove_squad_member",
    "update_squad",
    "update_squad_member",
    "user_managed_squad_ids",
    "user_squad_ids",
]
