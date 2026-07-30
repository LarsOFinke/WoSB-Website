from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build_feature import BuildFeatureDefinition


RESEARCH_UPGRADE_SLOT_CODE = "research_upgrade_slot"


def get_build_feature(
    db: Session,
    code: str,
    *,
    active_only: bool = True,
) -> BuildFeatureDefinition | None:
    statement = (
        select(BuildFeatureDefinition)
        .options(selectinload(BuildFeatureDefinition.effects))
        .where(BuildFeatureDefinition.code == code)
    )
    if active_only:
        statement = statement.where(BuildFeatureDefinition.is_active.is_(True))
    return db.scalar(statement)


def get_research_upgrade_feature(
    db: Session,
    *,
    enabled: bool,
) -> BuildFeatureDefinition | None:
    if not enabled:
        return None
    return get_build_feature(db, RESEARCH_UPGRADE_SLOT_CODE)
