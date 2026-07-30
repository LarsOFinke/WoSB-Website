from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.permissions.services.role_service import ensure_role_catalog
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.ship import Ship
from app.bootstrap.admin_user import seed_admin_user
from app.bootstrap.build_catalog import seed_build_option_catalog
from app.bootstrap.ship_catalog import (
    seed_ship_catalog,
    seed_ship_rate_weapon_class_rules,
    seed_ship_upgrade_effect_overrides,
    seed_ship_weapon_option_allowances,
    seed_ships,
    seed_weapon_definitions,
)
from app.bootstrap.system_catalog import seed_build_features, seed_fleets, seed_system_catalog


class SeedManager:
    """Orchestrate the idempotent production bootstrap catalog.

    Repository-owned records are loaded exclusively from ``backend/seeds``.
    This package contains only validation, synchronization and environment-based
    bootstrap logic.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self) -> None:
        seed_system_catalog(self.db)
        seed_ship_catalog(self.db)
        seed_build_option_catalog(self.db)
        seed_ship_upgrade_effect_overrides(self.db)
        seed_ship_weapon_option_allowances(self.db)

    def seed_override_counts(self) -> dict[str, int]:
        """Return repository-owned records intentionally protected from normal seeds."""

        models = {
            "categories": BuildItemCategory,
            "options": BuildItemOption,
            "ships": Ship,
        }
        return {
            name: int(
                self.db.scalar(
                    select(func.count()).select_from(model).where(
                        model.seed_key.is_not(None),
                        model.is_seed_overridden.is_(True),
                    )
                )
                or 0
            )
            for name, model in models.items()
        }

    def restore_repository_seed_defaults(self) -> dict[str, int]:
        """Release all repository-owned overrides before an explicit repair seed.

        Custom records have no ``seed_key`` and are never touched. The following
        regular seed run restores scalar values, relationships and sparse effect
        rows from the versioned JSON catalog.
        """

        models = {
            "categories": BuildItemCategory,
            "options": BuildItemOption,
            "ships": Ship,
        }
        restored: dict[str, int] = {}
        for name, model in models.items():
            rows = self.db.scalars(
                select(model).where(
                    model.seed_key.is_not(None),
                    model.is_seed_overridden.is_(True),
                )
            ).all()
            restored[name] = len(rows)
            for row in rows:
                row.is_seed_overridden = False
                row.seed_revision = None
                row.seed_checksum = None
        self.db.commit()
        return restored

    # Small explicit entry points are retained for admin restore operations and
    # focused tests. The implementation stays in responsibility-specific modules.
    def seed_role_catalog(self) -> None:
        ensure_role_catalog(self.db)
        self.db.commit()

    def seed_users(self) -> None:
        seed_admin_user(self.db)

    def seed_fleets(self) -> None:
        seed_fleets(self.db)

    def seed_weapon_slot_types(self) -> None:
        seed_weapon_definitions(self.db)
        seed_ship_rate_weapon_class_rules(self.db)

    def seed_ships(self) -> None:
        seed_ship_rate_weapon_class_rules(self.db)
        seed_ships(self.db)
        seed_ship_upgrade_effect_overrides(self.db)
        seed_ship_weapon_option_allowances(self.db)

    def seed_build_options(self) -> None:
        seed_build_features(self.db)
        seed_build_option_catalog(self.db)
        seed_ship_upgrade_effect_overrides(self.db)
        seed_ship_weapon_option_allowances(self.db)
