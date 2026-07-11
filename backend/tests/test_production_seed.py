from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.accounts.models.user import User
from app.modules.accounts.services.auth_service import create_user
from app.modules.builds.models.build import Build
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.calendar.models.fleet_event import FleetEvent
from app.modules.forum.models.forum import ForumThread
from app.modules.groups.models.group import Group
from app.modules.guides.models.guide import Guide
from app.modules.onboarding.models.newcomer_guide import NewcomerGuideBlock, NewcomerGuidePage
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.seeds.manager import SeedManager


def _count(db: Session, model: type) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def test_production_seed_bootstraps_only_system_and_master_data() -> None:
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
        manager.run()

        assert _count(db, User) == 1
        assert _count(db, Ship) > 0
        assert _count(db, BuildItemOption) > 0
        assert _count(db, Build) == 0
        assert _count(db, Guide) == 0
        assert _count(db, Group) == 0
        assert _count(db, FleetEvent) == 0
        assert _count(db, ForumThread) == 0
        assert _count(db, NewcomerGuidePage) == 0
        assert _count(db, NewcomerGuideBlock) == 0


def test_production_seed_is_idempotent_without_creating_example_activity() -> None:
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
        manager.run()
        master_counts = (_count(db, Ship), _count(db, BuildItemOption))

        manager.run()

        assert (_count(db, Ship), _count(db, BuildItemOption)) == master_counts
        for model in (Build, Guide, Group, FleetEvent, ForumThread, NewcomerGuidePage):
            assert _count(db, model) == 0
