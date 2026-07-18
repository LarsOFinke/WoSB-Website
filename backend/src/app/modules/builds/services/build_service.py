from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build import Build
from app.modules.builds.models.build_classification import BuildClassification
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.constants import BUILD_CLASSIFICATION_VALUES, BUILD_TYPE_VALUES
from app.modules.builds.services.build_validation import (
    BuildValidationError,
    validate_and_prepare_build,
)
from app.modules.ships.models.ship import Ship

__all__ = ["BuildValidationError", "create_build", "delete_build", "delete_user_build", "get_build", "list_builds", "list_user_builds", "update_user_build"]


def _build_query():
    return select(Build).options(
        selectinload(Build.slots).selectinload(BuildSlot.option),
        selectinload(Build.classifications),
    )

def list_builds(
    db: Session,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
    owner_id: int | None = None,
) -> list[Build]:
    statement = _build_query().join(Build.ship).order_by(Build.created_at.desc(), Build.id.desc())
    if search:
        like = f"%{search.strip()}%"
        statement = statement.where(
            Build.build_name.ilike(like)
            | Ship.name.ilike(like)
            | Build.build_type.ilike(like)
        )
    if build_type:
        normalized_type = build_type.strip().lower()
        if normalized_type in BUILD_TYPE_VALUES:
            statement = statement.where(Build.build_type == normalized_type)
    if classification:
        normalized_classification = classification.strip().lower()
        if normalized_classification in BUILD_CLASSIFICATION_VALUES:
            statement = statement.where(
                Build.classifications.any(BuildClassification.tag == normalized_classification)
            )
    if owner_id is not None:
        statement = statement.where(Build.owner_id == owner_id)
    return list(db.scalars(statement).unique().all())

def get_build(db: Session, build_id: int) -> Build | None:
    return db.scalar(_build_query().where(Build.id == build_id))

def _apply_build_payload(db_build: Build, build: BuildCreate, slots: list[BuildSlot]) -> None:
    db_build.build_name = build.build_name
    db_build.build_type = build.build_type
    db_build.ship_id = build.ship_id
    db_build.research_upgrade_slot_unlocked = build.research_upgrade_slot_unlocked
    db_build.sailors = build.sailors
    db_build.soldiers = build.soldiers
    db_build.musketeers = build.musketeers
    db_build.mercenaries = build.mercenaries
    db_build.details = build.details
    db_build.slots = slots
    db_build.classifications = [BuildClassification(tag=tag) for tag in build.classification_tags]

def create_build(db: Session, build: BuildCreate, owner_id: int | None = None) -> Build:
    _, slots = validate_and_prepare_build(db, build)
    db_build = Build(owner_id=owner_id)
    _apply_build_payload(db_build, build, slots)
    db.add(db_build)
    db.commit()
    return get_build(db, db_build.id) or db_build

def update_user_build(
    db: Session, build_id: int, user_id: int, build: BuildCreate
) -> Build | None:
    db_build = get_build(db, build_id)
    if db_build is None or db_build.owner_id != user_id or db_build.is_official_template:
        return None

    _, slots = validate_and_prepare_build(db, build)
    db_build.slots.clear()
    db.flush()
    _apply_build_payload(db_build, build, slots)
    db.add(db_build)
    db.commit()
    return get_build(db, db_build.id) or db_build

def delete_build(db: Session, build_id: int) -> bool:
    build = get_build(db, build_id)
    if build is None:
        return False
    db.delete(build)
    db.commit()
    return True

def list_user_builds(
    db: Session,
    user_id: int,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
) -> list[Build]:
    return list_builds(
        db,
        search=search,
        build_type=build_type,
        classification=classification,
        owner_id=user_id,
    )

def delete_user_build(db: Session, build_id: int, user_id: int) -> bool:
    build = get_build(db, build_id)
    if build is None or build.owner_id != user_id:
        return False
    db.delete(build)
    db.commit()
    return True
