from __future__ import annotations

from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_service import BuildValidationError, create_build
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.seeds.manager import SeedManager


@contextmanager
def seeded_session():
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()
        yield db


def _ship(db: Session, name: str = "Russia") -> Ship:
    ship = db.scalar(select(Ship).where(Ship.name == name))
    assert ship is not None
    return ship


def test_sails_and_lanterns_contribute_to_effective_build_stats() -> None:
    with seeded_session() as db:
        ship = _ship(db)
        build = create_build(
            db,
            BuildCreate(
                build_name="Equipment effects",
                ship_id=ship.id,
                sails="Elite Sails",
                lantern="Storm Lantern",
                sailors=ship.sailor_minimum,
            ),
        )

        assert build.ship_stats["sail_effects"] == {"speed_pct": 8}
        assert build.ship_stats["lantern_effects"] == {"speed_pct": 3}
        assert build.ship_stats["item_effects"]["speed_pct"] == 11
        assert build.ship_stats["effective_stats"]["speed_knots"] == pytest.approx(11.0)


def test_lantern_flat_effect_is_applied_server_side() -> None:
    with seeded_session() as db:
        ship = _ship(db)
        build = create_build(
            db,
            BuildCreate(
                build_name="Lantern hold effect",
                ship_id=ship.id,
                lantern="Golden Lantern",
                sailors=ship.sailor_minimum,
            ),
        )

        assert build.ship_stats["lantern_effects"] == {"hold_capacity": 1000}
        assert build.ship_stats["effective_stats"]["hold_capacity"] == ship.hold_capacity + 1000


def test_research_reward_unlocks_and_persists_fifth_upgrade_slot() -> None:
    with seeded_session() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "upgrade"))
        assert category is not None
        upgrade = db.scalar(
            select(BuildItemOption)
            .where(BuildItemOption.category_id == category.id, BuildItemOption.is_active.is_(True))
            .order_by(BuildItemOption.id)
        )
        assert upgrade is not None

        ship = Ship(
            name="Research Reward Test Ship",
            rate=5,
            ship_type="Test",
            durability=100,
            speed_knots=8,
            maneuverability=80,
            armor=1,
            hold_capacity=100,
            crew_capacity=20,
            sailor_minimum=0,
            displacement_tons=100,
            source="test",
            sail_slots=1,
            upgrade_slots=5,
            has_lantern=True,
            is_active=True,
        )
        db.add(ship)
        db.commit()

        with pytest.raises(BuildValidationError, match="research reward"):
            create_build(
                db,
                BuildCreate(
                    build_name="Locked fifth slot",
                    ship_id=ship.id,
                    upgrade_5=upgrade.name,
                ),
            )

        build = create_build(
            db,
            BuildCreate(
                build_name="Unlocked fifth slot",
                ship_id=ship.id,
                research_upgrade_slot_unlocked=True,
                upgrade_5=upgrade.name,
            ),
        )

        assert build.research_upgrade_slot_unlocked is True
        assert build.upgrade_5 == upgrade.name
        assert build.ship_stats["research_upgrade_slots"] == 1
        assert build.ship_stats["upgrade_slot_5_unlocked"] is True
        assert build.ship_stats["upgrade_slots_available"] == 5
