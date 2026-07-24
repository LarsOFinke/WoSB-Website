from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.fleet.models.fleet import Fleet
from app.modules.permissions.services.role_service import ensure_role_catalog
from app.bootstrap.admin_user import seed_admin_user
from app.bootstrap.catalog_loader import load_master_data_catalog


def seed_system_catalog(db: Session) -> None:
    """Seed the minimum operational records required by a fresh installation."""

    ensure_role_catalog(db)
    db.commit()
    seed_admin_user(db)
    seed_fleets(db)


def seed_fleets(db: Session) -> None:
    document = load_master_data_catalog().fleets
    fleet_rows = [row.model_dump(mode="json") for row in document.items]
    legacy_slugs = set(document.legacy_slugs)
    active_slugs = {str(row["slug"]) for row in fleet_rows}
    for fleet_data in fleet_rows:
        slug = str(fleet_data["slug"])
        existing = db.scalar(select(Fleet).where(Fleet.slug == slug))
        if existing is None:
            existing = db.scalar(select(Fleet).where(Fleet.slug.in_(legacy_slugs)))

        payload = {**fleet_data, "is_active": fleet_data.get("is_active", True)}
        if existing is None:
            db.add(Fleet(**payload))
            continue
        for field_name, value in payload.items():
            setattr(existing, field_name, value)

    for fleet in db.scalars(select(Fleet)).all():
        if fleet.slug not in active_slugs and fleet.sort_order >= 10:
            fleet.is_active = False
    db.commit()
