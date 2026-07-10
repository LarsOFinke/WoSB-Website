from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.accounts.services.auth_service import create_user
from app.modules.builds.models.build import Build
from app.modules.calendar.models.fleet_event import FleetEvent
from app.modules.forum.models.forum import ForumThread
from app.modules.groups.models.group import Group
from app.modules.guides.models.guide import Guide
from app.modules.registry import register_all_models
from app.seeds.manager import SeedManager
from app.seeds.starter_content import GUIDE_DATA, STARTER_BUILD_DATA


def test_production_seed_contains_curated_templates_without_fake_activity() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        create_user(db, username="seed-admin", password="strong-test-password", display_name="Seed Admin", role="admin")
        manager = SeedManager(db)
        manager.run()
        build_names = set(db.scalars(select(Build.build_name)).all())
        guide_names = set(db.scalars(select(Guide.title)).all())
        assert {row["build_name"] for row in STARTER_BUILD_DATA} <= build_names
        assert {row["title"] for row in GUIDE_DATA} <= guide_names
        assert db.scalar(select(Group.id).limit(1)) is None
        assert db.scalar(select(FleetEvent.id).limit(1)) is None
        assert db.scalar(select(ForumThread.id).limit(1)) is None


def test_seed_retires_untouched_legacy_demo_records_but_preserves_staff_edits() -> None:
    from datetime import datetime, timedelta

    from app.modules.calendar.models.fleet_event import FleetEvent
    from app.modules.forum.models.forum_post import ForumPost
    from app.modules.groups.models.group import Group
    from app.modules.onboarding.models.newcomer_guide import NewcomerGuideBlock, NewcomerGuidePage
    from app.seeds.legacy_demo_cleanup import cleanup_legacy_demo_content
    from app.seeds.newcomer_guide import LEGACY_DEFAULT_INTRO, seed_newcomer_guide

    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        admin = create_user(db, username="cleanup-admin", password="strong-test-password", display_name="Cleanup Admin", role="admin")
        ship = __import__("app.modules.ships.models.ship", fromlist=["Ship"]).Ship(
            name="Cleanup Ship", rate=7, ship_type="Test Ship", crew_capacity=10,
            sailor_minimum=1, upgrade_slots=1, sail_slots=1,
        )
        db.add(ship)
        db.flush()
        db.add(Build(
            build_name="Victory Defensive Line", build_type="defensive", ship_id=ship.id,
            owner_id=admin.id, details="Demo build for line/sustain play. The data model is normalized; slots reference the option catalog.",
        ))
        db.add(Guide(
            title="Port-Battle Line Basics", category="combat",
            summary="A compact starter doctrine for line discipline, focus calls and repair timing.",
            body="legacy", owner_id=admin.id,
        ))
        db.add(Guide(
            title="Trade Convoy Checklist", category="economy",
            summary="Staff rewrote this guide and wants to keep it.", body="custom", owner_id=admin.id,
        ))
        thread = ForumThread(
            title="Practice feedback: line turns and repair cadence", category="training", owner_id=admin.id,
        )
        thread.posts.append(ForumPost(body="Last training showed better focus fire, but our turn timing still spreads the line.", author_id=admin.id))
        db.add(thread)
        db.add(Group(
            title="Evening PvE Farming Run", focus="pve_farming",
            description="Relaxed fleet announcement for resources and routine fights.", max_members=6,
            allow_guests=False, owner_id=admin.id,
        ))
        now = datetime.utcnow()
        db.add(FleetEvent(
            title="Gunnery Training", category="training", description="Short practice block for arcs, chain shot timing and coordinated focus fire.",
            start_at=now, end_at=now + timedelta(hours=1), owner_id=admin.id,
        ))
        page = NewcomerGuidePage(id=1, title="New Captain Guide", intro=LEGACY_DEFAULT_INTRO, updated_by_id=admin.id)
        page.blocks.extend([
            NewcomerGuideBlock(block_type="text", title="Welcome aboard", body="legacy", sort_order=10),
            NewcomerGuideBlock(block_type="text", title="Staff custom block", body="keep", sort_order=15),
        ])
        db.add(page)
        db.commit()

        cleanup_legacy_demo_content(db)
        assert db.scalar(select(Build.id).where(Build.build_name == "Victory Defensive Line")) is None
        assert db.scalar(select(Guide.id).where(Guide.title == "Port-Battle Line Basics")) is None
        assert db.scalar(select(Guide.id).where(Guide.title == "Trade Convoy Checklist")) is not None
        assert db.scalar(select(ForumThread.id).where(ForumThread.title == "Practice feedback: line turns and repair cadence")) is None
        assert db.scalar(select(Group.id).where(Group.title == "Evening PvE Farming Run")) is None
        assert db.scalar(select(FleetEvent.id).where(FleetEvent.title == "Gunnery Training")) is None

        # Starter content must exist before progression resources are linked.
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()
        manager.seed_starter_content()
        seed_newcomer_guide(db)
        block_titles = {row.title for row in db.get(NewcomerGuidePage, 1).blocks}
        assert "Welcome aboard" not in block_titles
        assert "Staff custom block" in block_titles
        assert {row["title"] for row in __import__("app.seeds.newcomer_guide", fromlist=["PROGRESSION_BLOCKS"]).PROGRESSION_BLOCKS} <= block_titles
