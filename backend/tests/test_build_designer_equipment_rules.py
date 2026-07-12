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
from app.modules.builds.services.research_upgrade_reward import RESEARCH_UPGRADE_SLOT_EFFECTS
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.ship_upgrade_effect import ShipUpgradeEffectOverride
from app.seeds.catalog_sync import seed_key
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


SAIL_EFFECTS = {
    "Cheap Sails": {"speed_knots": 2},
    "Stitched Sails": {"speed_knots": 2.4},
    "Ultra-light Sails": {
        "speed_knots": 2.4,
        "cruising_maneuverability_pct": 15,
        "cruising_turn_speed_penalty_pct": -30,
    },
    "Storm Sails": {
        "speed_knots": 2.7,
        "strong_wind_cruising_speed_bonus_knots": 2.5,
    },
    "Elite Sails": {"speed_knots": 2.8},
    "Tacking Sails": {
        "speed_knots": 2.8,
        "turning_cruising_speed_bonus_knots": 2,
        "cruising_maneuverability_pct": -20,
    },
    "Reefed Sails": {
        "speed_knots": 2.9,
        "running_before_wind_speed_penalty_pct": -100,
        "broad_reach_cruising_speed_bonus_pct": -50,
    },
    "Tarpaulin Sails": {"speed_knots": 3.1, "maneuverability": -2},
    "Raiding Sails": {
        "speed_knots": 4.1,
        "cruising_maneuverability_pct": -20,
        "cruising_speed_gain_pct": -20,
    },
}

LANTERN_EFFECTS = {
    "Blue Lantern": {"speed_pct": 6},
    "Bright Lantern": {"hold_capacity_pct": 12},
    "Golden Lantern": {"speed_pct": 5, "armor_pct": 5, "damage_pct": 5},
    "Green Lantern": {"hull_hp_pct": 7},
    "Ice Lantern": {"speed_pct": 5, "hold_capacity_pct": 5, "hull_hp_pct": 5},
    "Lilac Lantern": {"turn_rate_pct": 7},
    "Red Lantern": {"turn_rate_pct": 5, "damage_pct": 5, "exp_loot_pct": 7},
    "White Lantern": {"exp_loot_pct": 10},
    "Yellow Lantern": {"damage_pct": 7},
}


def test_raiding_sails_apply_every_verified_tooltip_effect() -> None:
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

        assert build.ship_stats["sail_effects"] == SAIL_EFFECTS["Raiding Sails"]
        assert build.ship_stats["effective_stats"]["speed_knots"] == pytest.approx(
            ship.speed_knots + 4.1
        )
        assert build.ship_stats["effective_stats"]["cruising_maneuverability_pct"] == -20
        assert build.ship_stats["effective_stats"]["cruising_speed_gain_pct"] == -20
        assert build.ship_stats["upgrade_debuffs"]["cruising_maneuverability_pct"] == -20
        assert build.ship_stats["upgrade_debuffs"]["cruising_speed_gain_pct"] == -20


@pytest.mark.parametrize(("sail_name", "expected_effects"), SAIL_EFFECTS.items())
def test_every_verified_sail_is_forwarded_and_applied_server_side(
    sail_name: str,
    expected_effects: dict[str, int | float],
) -> None:
    with seeded_session() as db:
        ship = _ship(db)
        build = create_build(
            db,
            BuildCreate(
                build_name=f"{sail_name} calculation",
                ship_id=ship.id,
                sails=sail_name,
                sailors=ship.sailor_minimum,
            ),
        )

        stats = build.ship_stats
        assert stats["sail_effects"] == expected_effects
        assert stats["effective_stats"]["speed_knots"] == pytest.approx(
            round(ship.speed_knots + float(expected_effects["speed_knots"]), 1)
        )
        if "maneuverability" in expected_effects:
            assert stats["effective_stats"]["maneuverability"] == (
                ship.maneuverability + expected_effects["maneuverability"]
            )
        for key, value in expected_effects.items():
            if key not in {"speed_knots", "maneuverability"}:
                assert stats["effective_stats"][key] == value


@pytest.mark.parametrize(("lantern_name", "expected_effects"), LANTERN_EFFECTS.items())
def test_every_verified_lantern_is_forwarded_and_applied_server_side(
    lantern_name: str,
    expected_effects: dict[str, int | float],
) -> None:
    with seeded_session() as db:
        ship = _ship(db)
        build = create_build(
            db,
            BuildCreate(
                build_name=f"{lantern_name} calculation",
                ship_id=ship.id,
                lantern=lantern_name,
                sailors=ship.sailor_minimum,
            ),
        )

        stats = build.ship_stats
        assert stats["lantern_effects"] == expected_effects
        if "speed_pct" in expected_effects:
            assert stats["effective_stats"]["speed_knots"] == pytest.approx(
                round(ship.speed_knots * (1 + expected_effects["speed_pct"] / 100), 1)
            )
        if "hold_capacity_pct" in expected_effects:
            assert stats["effective_stats"]["hold_capacity"] == round(
                ship.hold_capacity * (1 + expected_effects["hold_capacity_pct"] / 100)
            )
        if "armor_pct" in expected_effects:
            assert stats["effective_stats"]["armor"] == pytest.approx(
                round(ship.armor * (1 + expected_effects["armor_pct"] / 100), 1)
            )
        if "hull_hp_pct" in expected_effects:
            assert stats["effective_stats"]["durability"] == round(
                ship.durability * (1 + expected_effects["hull_hp_pct"] / 100)
            )
        if "turn_rate_pct" in expected_effects:
            assert stats["effective_stats"]["maneuverability"] == round(
                ship.maneuverability * (1 + expected_effects["turn_rate_pct"] / 100)
            )
        for key in ("damage_pct", "exp_loot_pct"):
            if key in expected_effects:
                assert stats["effective_stats"][key] == expected_effects[key]


def test_build_catalog_api_forwards_verified_sail_and_lantern_effects() -> None:
    from app.modules.builds.services.build_option_service import list_build_options

    with seeded_session() as db:
        catalog = list_build_options(db)
        sails = {option.name: option.stat_effects for option in catalog.options["sail"]}
        lanterns = {option.name: option.stat_effects for option in catalog.options["lantern"]}

        assert sails == SAIL_EFFECTS
        assert lanterns == LANTERN_EFFECTS


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


def test_reseeding_repairs_incomplete_non_overridden_equipment_effects() -> None:
    with seeded_session() as db:
        category_ids = {
            row.key: row.id
            for row in db.scalars(
                select(BuildItemCategory).where(BuildItemCategory.key.in_(["sail", "lantern"]))
            ).all()
        }
        stitched = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category_ids["sail"],
                BuildItemOption.name == "Stitched Sails",
            )
        )
        golden = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category_ids["lantern"],
                BuildItemOption.name == "Golden Lantern",
            )
        )
        assert stitched is not None and golden is not None

        stitched.effects.clear()
        stitched.seed_checksum = "incomplete-sail-catalog"
        golden.effects.clear()
        golden.seed_checksum = "incomplete-lantern-catalog"
        db.commit()

        SeedManager(db).seed_build_options()
        db.refresh(stitched)
        db.refresh(golden)

        assert stitched.stat_effects == {"speed_knots": 2.4}
        assert golden.stat_effects == {"speed_pct": 5, "armor_pct": 5, "damage_pct": 5}
        assert stitched.is_seed_overridden is False
        assert golden.is_seed_overridden is False


def test_reseed_deactivates_superseded_sail_and_lantern_catalog_entries() -> None:
    with seeded_session() as db:
        categories = {
            row.key: row
            for row in db.scalars(
                select(BuildItemCategory).where(BuildItemCategory.key.in_(["sail", "lantern"]))
            ).all()
        }
        legacy_sail = BuildItemOption(
            category_id=categories["sail"].id,
            name="Imported Sails",
            source="legacy catalog",
            notes="Retained for historical builds.",
            option_kind="sail",
            seed_key=seed_key("build-option", "sail", "imported"),
            seed_revision="legacy",
            seed_checksum="legacy",
            is_active=True,
        )
        legacy_lantern = BuildItemOption(
            category_id=categories["lantern"].id,
            name="Storm Lantern",
            source="legacy catalog",
            notes="Retained for historical builds.",
            option_kind="lantern",
            seed_key=seed_key("build-option", "lantern", "storm"),
            seed_revision="legacy",
            seed_checksum="legacy",
            is_active=True,
        )
        db.add_all([legacy_sail, legacy_lantern])
        db.commit()
        sail_id = legacy_sail.id
        lantern_id = legacy_lantern.id

        SeedManager(db).seed_build_options()
        db.refresh(legacy_sail)
        db.refresh(legacy_lantern)

        assert legacy_sail.id == sail_id
        assert legacy_lantern.id == lantern_id
        assert legacy_sail.is_active is False
        assert legacy_lantern.is_active is False
        assert legacy_sail.seed_revision is None
        assert legacy_lantern.seed_revision is None


def test_current_event_leopard_and_ice_lantern_are_calculated_together() -> None:
    with seeded_session() as db:
        ship = _ship(db, "Leopard")
        build = create_build(
            db,
            BuildCreate(
                build_name="Leopard with Ice Lantern",
                ship_id=ship.id,
                lantern="Ice Lantern",
                sailors=ship.sailor_minimum,
            ),
        )

        assert build.ship_stats["lantern_effects"] == {
            "speed_pct": 5,
            "hold_capacity_pct": 5,
            "hull_hp_pct": 5,
        }
        assert build.ship_stats["effective_stats"]["speed_knots"] == pytest.approx(19.6)
        assert build.ship_stats["effective_stats"]["hold_capacity"] == 17325
        assert build.ship_stats["effective_stats"]["durability"] == 2142


def test_structural_expansion_and_special_ship_stack_to_eighth_upgrade_slot() -> None:
    with seeded_session() as db:
        structural = db.scalar(
            select(BuildItemOption).where(BuildItemOption.name == "Structural Expansion")
        )
        helm = db.scalar(
            select(BuildItemOption).where(BuildItemOption.name == "Maneuverable Helm")
        )
        assert structural is not None and helm is not None
        assert structural.stat_effects["extra_upgrade_slots"] == 2

        special_ship = Ship(
            name="Eight Slot Test Ship",
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
            # Normal ships use 5; 6 denotes the ship-specific extra slot.
            upgrade_slots=6,
            has_lantern=True,
            is_active=True,
        )
        normal_ship = Ship(
            name="Seven Slot Control Ship",
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
        db.add_all([special_ship, normal_ship])
        db.commit()

        normal_build = create_build(
            db,
            BuildCreate(
                build_name="Normal ship reaches slot seven",
                ship_id=normal_ship.id,
                research_upgrade_slot_unlocked=True,
                upgrade_5=structural.name,
                upgrade_7=helm.name,
            ),
        )
        assert normal_build.ship_stats["upgrade_slots_available"] == 7
        assert normal_build.ship_stats["upgrade_slot_7_available"] is True
        assert normal_build.ship_stats["upgrade_slot_8_available"] is False

        with pytest.raises(BuildValidationError, match="Upgrade slot 8 requires"):
            create_build(
                db,
                BuildCreate(
                    build_name="Normal ship cannot use slot eight",
                    ship_id=normal_ship.id,
                    research_upgrade_slot_unlocked=True,
                    upgrade_5=structural.name,
                    upgrade_8=helm.name,
                ),
            )

        build = create_build(
            db,
            BuildCreate(
                build_name="Full eight slot stack",
                ship_id=special_ship.id,
                research_upgrade_slot_unlocked=True,
                # Slot 5 already exists through research + the ship extra, so
                # Structural Expansion may be installed there without circular
                # self-unlocking. Its full +2 tooltip value unlocks slots 7-8.
                upgrade_5=structural.name,
                upgrade_8=helm.name,
            ),
        )

        stats = build.ship_stats
        assert build.upgrade_8 == helm.name
        assert stats["extra_upgrade_slots"] == 2
        assert stats["expansion_upgrade_slots"] == 2
        assert stats["research_upgrade_slots"] == 1
        assert stats["ship_extra_upgrade_slots"] == 1
        assert stats["upgrade_slot_7_available"] is True
        assert stats["upgrade_slot_8_available"] is True
        assert stats["upgrade_slots_available"] == 8


def test_ship_specific_structural_expansion_value_controls_slot_unlock() -> None:
    with seeded_session() as db:
        structural = db.scalar(
            select(BuildItemOption).where(BuildItemOption.name == "Structural Expansion")
        )
        helm = db.scalar(
            select(BuildItemOption).where(BuildItemOption.name == "Maneuverable Helm")
        )
        assert structural is not None and helm is not None

        ship = Ship(
            name="Structural Override Test Ship",
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
            upgrade_slots=6,
            has_lantern=True,
            is_active=True,
        )
        db.add(ship)
        db.flush()
        ship.upgrade_effect_overrides.append(
            ShipUpgradeEffectOverride(
                option_id=structural.id,
                effect_key="extra_upgrade_slots",
                # This ship-specific override grants only one rack position.
                effect_value=1,
            )
        )
        db.commit()

        allowed = create_build(
            db,
            BuildCreate(
                build_name="Override still permits slot seven",
                ship_id=ship.id,
                research_upgrade_slot_unlocked=True,
                upgrade_5=structural.name,
                upgrade_7=helm.name,
            ),
        )
        assert allowed.ship_stats["expansion_upgrade_slots"] == 1
        assert allowed.ship_stats["upgrade_slots_available"] == 7

        with pytest.raises(BuildValidationError, match="Upgrade slot 8 requires"):
            create_build(
                db,
                BuildCreate(
                    build_name="Override blocks eighth slot",
                    ship_id=ship.id,
                    research_upgrade_slot_unlocked=True,
                    upgrade_5=structural.name,
                    upgrade_8=helm.name,
                ),
            )
