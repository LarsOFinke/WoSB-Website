from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.builds.models.build_feature import BuildFeatureDefinition
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.ships.models.ship import Ship

from .errors import BuildValidationError
from .validator import BuildValidator


def validate_and_prepare_build(
    db: Session, build: BuildCreate
) -> tuple[Ship, list[BuildSlot], BuildFeatureDefinition | None]:
    return BuildValidator(db).validate_and_prepare(build)


__all__ = ["BuildValidationError", "BuildValidator", "validate_and_prepare_build"]
