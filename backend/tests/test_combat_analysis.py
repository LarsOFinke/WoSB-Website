from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.bootstrap.manager import SeedManager
from app.db.base import Base
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.schemas.master_data import MasterDataOptionCreate, MasterDataOptionUpdate
from app.modules.admin.services.master_data_service import create_option, list_options, update_option
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.weapon_performance import WeaponPerformanceProfile
from app.modules.builds.services.build_option_service import list_build_options
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship


def _seeded_db() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    create_user(
        db,
        username="combat-analysis-admin",
        password="strong-test-password",
        display_name="Combat Analysis Admin",
        role="admin",
    )
    SeedManager(db).run()
    return db


def test_weapon_performance_is_normalized_and_seeded_from_verified_cannon_data() -> None:
    with _seeded_db() as db:
        inspector = inspect(db.bind)
        assert "weapon_performance_profiles" in inspector.get_table_names()
        assert {column["name"] for column in inspector.get_columns("weapon_performance_profiles")} == {
            "option_id",
            "base_damage",
            "reload_seconds",
        }
        assert inspector.get_pk_constraint("weapon_performance_profiles")["constrained_columns"] == [
            "option_id"
        ]
        assert inspector.get_foreign_keys("weapon_performance_profiles")[0]["referred_table"] == (
            "build_item_options"
        )

        profiles = list(db.scalars(select(WeaponPerformanceProfile)).all())
        assert len(profiles) == 21
        rusty = db.scalar(
            select(BuildItemOption).where(BuildItemOption.name == "6-pdr Rusty Cannon")
        )
        zeus = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Zeus"))
        assert rusty is not None and rusty.weapon_performance is not None
        assert rusty.weapon_performance.base_damage == 13
        assert rusty.weapon_performance.reload_seconds == 10.5
        assert zeus is not None and zeus.weapon_performance is None


def test_ship_specific_build_catalog_exposes_weapon_performance_without_duplication() -> None:
    with _seeded_db() as db:
        ship = next(
            (
                row
                for row in db.scalars(
                    select(Ship).where(Ship.is_active.is_(True)).order_by(Ship.rate.desc(), Ship.id)
                ).all()
                if row.broadside_weapon_capacity > 0
            ),
            None,
        )
        assert ship is not None

        catalog = list_build_options(db, ship_id=ship.id)
        rusty = next(
            option
            for option in catalog.options["weapon"]
            if option.name == "6-pdr Rusty Cannon"
        )
        assert rusty.weapon_performance is not None
        assert rusty.weapon_performance.model_dump() == {
            "base_damage": 13.0,
            "reload_seconds": 10.5,
        }


def test_staff_master_data_can_create_update_and_clear_weapon_performance() -> None:
    with _seeded_db() as db:
        weapon_category = db.scalar(
            select(BuildItemCategory).where(BuildItemCategory.key == "weapon")
        )
        assert weapon_category is not None

        created = create_option(
            db,
            MasterDataOptionCreate(
                category_id=weapon_category.id,
                name="Fleet Test Cannon",
                source="verified fleet test",
                notes=None,
                image_url=None,
                option_kind="cannon",
                weapon_class="light",
                weapon_caliber_inches=6,
                weapon_performance={"base_damage": 12, "reload_seconds": 8},
                stat_effects={},
                allowed_slot_types=["weapon_port", "weapon_starboard"],
                sort_order=9990,
                is_active=True,
            ),
        )
        assert created.weapon_performance is not None
        assert created.weapon_performance.base_damage == 12

        updated = update_option(
            db,
            created.id,
            MasterDataOptionUpdate(
                category_id=weapon_category.id,
                name="Fleet Test Cannon",
                source="verified fleet test v2",
                notes=None,
                image_url=None,
                option_kind="cannon",
                weapon_class="light",
                weapon_caliber_inches=6,
                weapon_performance={"base_damage": 13.5, "reload_seconds": 7.5},
                stat_effects={},
                allowed_slot_types=["weapon_port", "weapon_starboard"],
                sort_order=9990,
                is_active=True,
            ),
        )
        assert updated.weapon_performance is not None
        assert updated.weapon_performance.base_damage == 13.5
        assert updated.weapon_performance.reload_seconds == 7.5

        cleared = update_option(
            db,
            created.id,
            MasterDataOptionUpdate(
                category_id=weapon_category.id,
                name="Fleet Test Cannon",
                source="verified fleet test v2",
                notes=None,
                image_url=None,
                option_kind="cannon",
                weapon_class="light",
                weapon_caliber_inches=6,
                weapon_performance=None,
                stat_effects={},
                allowed_slot_types=["weapon_port", "weapon_starboard"],
                sort_order=9990,
                is_active=True,
            ),
        )
        assert cleared.weapon_performance is None
        reloaded = next(row for row in list_options(db, search="Fleet Test Cannon"))
        assert reloaded.weapon_performance is None
