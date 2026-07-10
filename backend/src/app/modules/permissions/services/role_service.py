from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.fleet_role import FleetRole
from app.core.site_role import SiteRole
from app.modules.permissions.models.role import FleetRoleDefinition, SiteRoleDefinition, SquadRoleDefinition

SITE_ROLE_CATALOG = (
    {"code": SiteRole.USER.value, "label": "User", "rank": 10, "is_staff": False, "can_manage_system": False},
    {"code": SiteRole.MODERATOR.value, "label": "Moderator", "rank": 50, "is_staff": True, "can_manage_system": False},
    {"code": SiteRole.ADMIN.value, "label": "Administrator", "rank": 100, "is_staff": True, "can_manage_system": True},
)
FLEET_ROLE_CATALOG = (
    {"code": FleetRole.MEMBER.value, "label": "Fleet Member", "rank": 10, "is_leadership": False, "can_manage_fleet": False, "can_manage_members": False},
    {"code": FleetRole.LIEUTENANT.value, "label": "Fleet Lieutenant", "rank": 60, "is_leadership": True, "can_manage_fleet": True, "can_manage_members": True},
    {"code": FleetRole.ADMIRAL.value, "label": "Fleet Admiral", "rank": 80, "is_leadership": True, "can_manage_fleet": True, "can_manage_members": True},
)
SQUAD_ROLE_CATALOG = (
    {"code": "member", "label": "Squad Member", "rank": 10, "can_manage_roster": False, "can_manage_events": False},
    {"code": "officer", "label": "Squad Officer", "rank": 50, "can_manage_roster": True, "can_manage_events": True},
    {"code": "leader", "label": "Squad Leader", "rank": 80, "can_manage_roster": True, "can_manage_events": True},
)


def _sync_catalog(db: Session, model, rows: tuple[dict[str, object], ...]) -> None:
    existing = {row.code: row for row in db.scalars(select(model)).all()}
    for payload in rows:
        code = str(payload["code"])
        row = existing.get(code)
        if row is None:
            db.add(model(**payload))
            continue
        for key, value in payload.items():
            setattr(row, key, value)
    db.flush()


def ensure_role_catalog(db: Session) -> None:
    _sync_catalog(db, SiteRoleDefinition, SITE_ROLE_CATALOG)
    _sync_catalog(db, FleetRoleDefinition, FLEET_ROLE_CATALOG)
    _sync_catalog(db, SquadRoleDefinition, SQUAD_ROLE_CATALOG)


def _get_or_create_role(db: Session, model, catalog: tuple[dict[str, object], ...], code: str):
    with db.no_autoflush:
        row = db.scalar(select(model).where(model.code == code))
    if row is not None:
        return row
    payload = next((item for item in catalog if item["code"] == code), None)
    if payload is None:
        raise ValueError(f"Unknown role: {code}")
    row = model(**payload)
    db.add(row)
    # Flush only the lookup row. Pending memberships/users may still be
    # waiting for this foreign key and must not be flushed prematurely.
    db.flush([row])
    return row


def get_site_role(db: Session, code: str) -> SiteRoleDefinition:
    return _get_or_create_role(db, SiteRoleDefinition, SITE_ROLE_CATALOG, code)


def get_fleet_role(db: Session, code: str) -> FleetRoleDefinition:
    return _get_or_create_role(db, FleetRoleDefinition, FLEET_ROLE_CATALOG, code)


def get_squad_role(db: Session, code: str) -> SquadRoleDefinition:
    return _get_or_create_role(db, SquadRoleDefinition, SQUAD_ROLE_CATALOG, code)


def assign_site_role(db: Session, user, code: str) -> None:
    user.site_role = get_site_role(db, code)


def assign_fleet_role_definition(db: Session, membership, code: str) -> None:
    membership.fleet_role = get_fleet_role(db, code)


def assign_squad_role(db: Session, member, code: str) -> None:
    member.squad_role = get_squad_role(db, code)
