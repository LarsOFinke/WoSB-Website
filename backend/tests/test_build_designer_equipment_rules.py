from __future__ import annotations

from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_service import BuildValidationError, create_build
from app.modules.builds.services.research_upgrade_reward import RESEARCH_UPGRADE_SLOT_EFFECTS
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


def test_raiding_sails_apply_flat_speed_and_cruising_gain_debuff() -> None:
    with seeded_session() as db:
        ship = _ship(db)
        build = create_build(
            db,
            BuildCreate(
                build_name="Raiding sails tooltip values",
                ship_id=ship.id,
                sails="Raiding Sails",
                sailors=ship.sailor_minimum,
            ),
        )

        assert build.ship_stats["sail_effects"] == {
            "cruising_speed_gain_pct": -20,
            "speed_knots": 4.1,
        }
        assert build.ship_stats["effective_stats"]["speed_knots"] == pytest.approx(
            ship.speed_knots + 4.1
        )
        assert build.ship_stats["effective_stats"]["cruising_speed_gain_pct"] == -20
        assert build.ship_stats["upgrade_debuffs"]["cruising_speed_gain_pct"] == -20


def test_lantern_can_be_replaced_and_custom_effect_is_applied_server_side() -> None:
    with seeded_session() as db:
        ship = _ship(db)
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "lantern"))
        assert category is not None
        golden = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Golden Lantern",
            )
        )
        assert golden is not None
        golden.effects.append(BuildItemEffect(effect_key="hold_capacity", effect_value=1000))
        db.commit()

        golden_build = create_build(
            db,
            BuildCreate(
                build_name="Golden lantern",
                ship_id=ship.id,
                lantern="Golden Lantern",
                sailors=ship.sailor_minimum,
            ),
        )
        storm_build = create_build(
            db,
            BuildCreate(
                build_name="Storm lantern replacement",
                ship_id=ship.id,
                lantern="Storm Lantern",
                sailors=ship.sailor_minimum,
            ),
        )

        assert golden_build.lantern == "Golden Lantern"
        assert golden_build.ship_stats["lantern_effects"] == {"hold_capacity": 1000}
        assert golden_build.ship_stats["effective_stats"]["hold_capacity"] == ship.hold_capacity + 1000
        assert storm_build.lantern == "Storm Lantern"
        assert storm_build.ship_stats["lantern_effects"] == {}


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
        assert build.ship_stats["research_upgrade_slot_effects"] == RESEARCH_UPGRADE_SLOT_EFFECTS


def test_research_reward_debuffs_are_applied_to_live_and_saved_stats() -> None:
    with seeded_session() as db:
        ship = Ship(
            name="Research Debuff Test Ship",
            rate=5,
            ship_type="Test",
            durability=100,
            speed_knots=8,
            maneuverability=80,
            armor=10,
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

        build = create_build(
            db,
            BuildCreate(
                build_name="Research penalties",
                ship_id=ship.id,
                research_upgrade_slot_unlocked=True,
                sailors=18,
            ),
        )

        stats = build.ship_stats
        assert stats["research_upgrade_slot_effects"] == {
            "hull_hp_pct": -10,
            "speed_pct": -10,
            "turn_rate_pct": -10,
            "armor_pct": -10,
            "hold_capacity_pct": -10,
            "crew_capacity_pct": -10,
        }
        assert stats["effective_stats"] == {
            **stats["effective_stats"],
            "durability": 90,
            "speed_knots": 7.2,
            "maneuverability": 72,
            "armor": 9.0,
            "hold_capacity": 90,
            "crew_capacity": 18,
        }
        assert stats["effective_crew_capacity"] == 18
        assert all(value == -10 for value in stats["research_upgrade_slot_effects"].values())

        with pytest.raises(BuildValidationError, match="effective ship capacity"):
            create_build(
                db,
                BuildCreate(
                    build_name="Research penalty validation",
                    ship_id=ship.id,
                    research_upgrade_slot_unlocked=True,
                    sailors=19,
                ),
            )
