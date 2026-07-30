from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.fleet.models.fleet import Fleet
from app.modules.permissions.services.role_service import ensure_role_catalog
from app.modules.builds.services.build_role_service import ensure_default_build_roles
from app.modules.builds.models.build_feature import BuildFeatureDefinition, BuildFeatureEffect
from app.bootstrap.admin_user import seed_admin_user
from app.bootstrap.catalog_loader import load_master_data_catalog


def seed_system_catalog(db: Session) -> None:
    """Seed the minimum operational records required by a fresh installation."""

    ensure_role_catalog(db)
    ensure_default_build_roles(db)
    seed_build_features(db)
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


def seed_build_features(db: Session) -> None:
    document = load_master_data_catalog().build_rules
    active_codes = {row.code for row in document.build_features}
    for item in document.build_features:
        feature = db.scalar(
            select(BuildFeatureDefinition).where(BuildFeatureDefinition.code == item.code)
        )
        if feature is None:
            feature = BuildFeatureDefinition(code=item.code, label=item.label)
            db.add(feature)
            db.flush()
        feature.label = item.label
        feature.upgrade_slots_granted = item.upgrade_slots_granted
        feature.is_active = True
        current = {row.effect_key: row for row in feature.effects}
        for effect_key, effect_value in item.stat_effects.items():
            row = current.get(effect_key)
            if row is None:
                feature.effects.append(
                    BuildFeatureEffect(effect_key=effect_key, effect_value=float(effect_value))
                )
            else:
                row.effect_value = float(effect_value)
        for effect_key, row in current.items():
            if effect_key not in item.stat_effects:
                feature.effects.remove(row)
    for feature in db.scalars(select(BuildFeatureDefinition)).all():
        if feature.code not in active_codes:
            feature.is_active = False
    db.commit()
