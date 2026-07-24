from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bootstrap.catalog_loader import load_master_data_catalog
from app.modules.permissions.models.role import FleetRoleDefinition, SiteRoleDefinition, SquadRoleDefinition


def _catalog_rows(name: str) -> tuple[dict[str, object], ...]:
    document = load_master_data_catalog().roles
    rows = getattr(document, name)
    return tuple(row.model_dump(mode="json") for row in rows)


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
    _sync_catalog(db, SiteRoleDefinition, _catalog_rows("site_roles"))
    _sync_catalog(db, FleetRoleDefinition, _catalog_rows("fleet_roles"))
    _sync_catalog(db, SquadRoleDefinition, _catalog_rows("squad_roles"))


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
    db.flush([row])
    return row


def get_site_role(db: Session, code: str) -> SiteRoleDefinition:
    return _get_or_create_role(db, SiteRoleDefinition, _catalog_rows("site_roles"), code)


def get_fleet_role(db: Session, code: str, *, include_inactive: bool = False) -> FleetRoleDefinition:
    row = db.scalar(select(FleetRoleDefinition).where(FleetRoleDefinition.code == code))
    if row is not None:
        if not row.is_active and not include_inactive:
            raise ValueError(f"Inactive fleet role: {code}")
        return row
    return _get_or_create_role(db, FleetRoleDefinition, _catalog_rows("fleet_roles"), code)


def get_squad_role(db: Session, code: str) -> SquadRoleDefinition:
    return _get_or_create_role(db, SquadRoleDefinition, _catalog_rows("squad_roles"), code)


def assign_site_role(db: Session, user, code: str) -> None:
    user.site_role = get_site_role(db, code)


def assign_fleet_role_definition(db: Session, membership, code: str) -> None:
    membership.fleet_role = get_fleet_role(db, code)


def assign_squad_role(db: Session, member, code: str) -> None:
    member.squad_role = get_squad_role(db, code)
