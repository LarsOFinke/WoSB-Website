from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.accounts.services.auth_service import create_user
from app.modules.builds.models.build import Build
from app.modules.registry import register_all_models
from app.seeds.manager import SeedManager


def test_demo_builds_seed_against_current_ship_and_option_catalog() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        create_user(
            db,
            username="seed-admin",
            password="strong-test-password",
            display_name="Seed Admin",
            role="admin",
        )
        manager = SeedManager(db)
        manager.seed_ships()
        manager.seed_build_options()
        manager.seed_demo_builds()

        builds = db.scalars(select(Build).order_by(Build.build_name)).unique().all()
        assert [build.build_name for build in builds] == [
            "Adventure Mortar Support",
            "Surprise Gunnery Scout",
            "Victory Defensive Line",
        ]
