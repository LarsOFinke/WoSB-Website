from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.services.master_data_service import restore_ship_seed
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.ship_upgrade_effect import ShipUpgradeEffectOverride
from app.bootstrap.manager import SeedManager


def _seeded_db() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine, expire_on_commit=False)
    create_user(
        db,
        username="owned-ship-seed-admin",
        password="strong-test-password",
        display_name="Owned Ship Seed Admin",
        role="admin",
    )
    SeedManager(db).run()
    return db


def _option(db: Session, name: str) -> BuildItemOption:
    option = db.scalar(select(BuildItemOption).where(BuildItemOption.name == name))
    assert option is not None
    return option


def _ship(db: Session, name: str) -> Ship:
    ship = db.scalar(select(Ship).where(Ship.name == name))
    assert ship is not None
    return ship


def test_seeded_upgrade_values_follow_the_three_audited_ship_size_tiers() -> None:
    with _seeded_db() as db:
        reinforced_masts = _option(db, "Reinforced Masts")
        teak_frames = _option(db, "Teak Frames")

        adventure = _ship(db, "Adventure")
        assert effective_upgrade_effects(reinforced_masts, adventure) == {
            "speed_knots": 0.4,
            "sail_efficiency": 0.8,
        }
        assert effective_upgrade_effects(teak_frames, adventure) == {
            "armor": 1,
            "crew_capacity": 14,
            "turn_rate_pct": -6,
        }

        anson = _ship(db, "Anson")
        assert anson.upgrade_effect_overrides == []
        assert effective_upgrade_effects(reinforced_masts, anson) == {
            "speed_knots": 0.5,
            "sail_efficiency": 1,
        }
        assert effective_upgrade_effects(teak_frames, anson) == {
            "armor": 1.5,
            "crew_capacity": 10,
            "turn_rate_pct": -6,
        }

        black_prince = _ship(db, "Black Prince")
        assert effective_upgrade_effects(reinforced_masts, black_prince) == {
            "speed_knots": 0.6,
            "sail_efficiency": 1.2,
        }
        assert effective_upgrade_effects(teak_frames, black_prince) == {
            "armor": 2,
            "crew_capacity": 6,
            "turn_rate_pct": -6,
        }


def test_seeded_combat_upgrade_values_follow_current_ship_screenshots() -> None:
    with _seeded_db() as db:
        ammunition_cradles = _option(db, "Ammunition Cradles")
        reinforced_cannons = _option(db, "Reinforced Cannons")

        assert effective_upgrade_effects(ammunition_cradles, _ship(db, "Azov")) == {
            "reload_pct": 18,
        }
        assert effective_upgrade_effects(ammunition_cradles, _ship(db, "Santisima Trinidad")) == {
            "reload_pct": 18,
        }
        assert effective_upgrade_effects(reinforced_cannons, _ship(db, "Firestorm")) == {
            "bow_stern_weapon_damage_pct": 35,
        }
        assert effective_upgrade_effects(reinforced_cannons, _ship(db, "Sovereign")) == {
            "bow_stern_weapon_damage_pct": 61,
        }
        assert effective_upgrade_effects(reinforced_cannons, _ship(db, "Azov")) == {
            "bow_stern_weapon_damage_pct": 61,
        }
        assert effective_upgrade_effects(reinforced_cannons, _ship(db, "Santisima Trinidad")) == {
            "bow_stern_weapon_damage_pct": 87,
        }
        assert effective_upgrade_effects(reinforced_cannons, _ship(db, "Savannah")) == {
            "bow_stern_weapon_damage_pct": 121,
        }


def test_admin_ship_override_survives_bootstrap_and_restore_reinstates_seed_values() -> None:
    with _seeded_db() as db:
        ship = _ship(db, "Adventure")
        reinforced_masts = _option(db, "Reinforced Masts")

        ship.is_seed_overridden = True
        speed_override = next(
            row
            for row in ship.upgrade_effect_overrides
            if row.option_id == reinforced_masts.id and row.effect_key == "speed_knots"
        )
        speed_override.effect_value = 9.9
        db.commit()

        SeedManager(db).run()
        preserved = _ship(db, "Adventure")
        assert effective_upgrade_effects(reinforced_masts, preserved)["speed_knots"] == 9.9

        restored = restore_ship_seed(db, ship.id)
        restored_reinforced = next(
            row
            for row in restored.upgrade_effect_overrides
            if row.option_name == "Reinforced Masts"
        )
        assert restored_reinforced.effective_stat_effects == {
            "speed_knots": 0.4,
            "sail_efficiency": 0.8,
        }
        assert restored.is_seed_overridden is False
