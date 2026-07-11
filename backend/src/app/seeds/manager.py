from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.permissions.services.role_service import ensure_role_catalog
from app.seeds.build_option_catalog import seed_build_option_catalog
from app.seeds.ship_catalog import seed_ship_catalog, seed_ships, seed_weapon_definitions
from app.seeds.system_catalog import seed_fleets, seed_system_catalog
from app.seeds.users import seed_admin_user


class SeedManager:
    """Orchestrate the idempotent production bootstrap catalog.

    Seed modules intentionally contain only operational defaults and verified
    master data. User-facing example content belongs in tests or documentation,
    never in a production seed run.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self) -> None:
        seed_system_catalog(self.db)
        seed_ship_catalog(self.db)
        seed_build_option_catalog(self.db)

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

    def seed_ships(self) -> None:
        seed_ships(self.db)

    def seed_build_options(self) -> None:
        seed_build_option_catalog(self.db)
