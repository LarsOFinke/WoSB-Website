from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.schemas.master_data import (
    MasterDataOptionCreate,
    MasterDataOptionUpdate,
    MasterDataShipUpdate,
)
from app.modules.admin.services.master_data_service import (
    create_option,
    list_options,
    list_ships,
    restore_option_seed,
    restore_ship_seed,
    update_option,
    update_ship,
)
from app.modules.builds.models.build import Build
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.registry import register_all_models
from app.modules.guides.models.guide import Guide
from app.modules.ships.models.ship import Ship
from app.seeds.catalog_sync import CUSTOM_MASTER_DATA_REVISION
from app.seeds.manager import SeedManager
from main import app


def _seeded_db() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    create_user(
        db,
        username="master-data-seed-admin",
        password="strong-test-password",
        display_name="Master Data Admin",
        role="admin",
    )
    SeedManager(db).run()
    return db


def test_admin_overrides_survive_seed_and_can_be_restored() -> None:
    with _seeded_db() as db:
        option = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Copper Plating"))
        assert option is not None
        update_option(
            db,
            option.id,
            MasterDataOptionUpdate(
                category_id=option.category_id,
                name=option.name,
                source="manual audit",
                notes="Fleet-specific tuning",
                image_url="/uploads/copper-plating.webp",
                option_kind=option.option_kind,
                weapon_class=option.weapon_class_code,
                weapon_caliber_inches=option.weapon_caliber_inches,
                stat_effects={"water_fire_protection_pct": 99},
                allowed_slot_types=option.allowed_slots,
                sort_order=option.sort_order,
                is_active=True,
            ),
        )
        SeedManager(db).seed_build_options()
        preserved = next(row for row in list_options(db, search="Copper Plating") if row.id == option.id)
        assert preserved.stat_effects == {"water_fire_protection_pct": 99.0}
        assert preserved.image_url == "/uploads/copper-plating.webp"
        assert preserved.seed_status == "overridden"

        restored = restore_option_seed(db, option.id)
        assert restored.stat_effects == {
            "water_fire_protection_pct": 25.0,
            "explosive_fire_ship_protection_pct": 30.0,
        }
        assert restored.image_url is None
        assert restored.seed_status == "seeded"

        ship = db.scalar(select(Ship).where(Ship.name == "Firestorm"))
        assert ship is not None
        current = next(row for row in list_ships(db, search="Firestorm") if row.id == ship.id)
        update_ship(
            db,
            ship.id,
            MasterDataShipUpdate(
                **{
                    **current.model_dump(exclude={
                        "id", "weapon_layout", "seed_key", "seed_revision", "is_seed_overridden",
                        "seed_status", "created_at", "updated_at",
                    }),
                    "speed_knots": 42,
                    "image_url": "/uploads/firestorm.webp",
                }
            ),
        )
        SeedManager(db).seed_ships()
        preserved_ship = next(row for row in list_ships(db, search="Firestorm") if row.id == ship.id)
        assert preserved_ship.speed_knots == 42
        assert preserved_ship.image_url == "/uploads/firestorm.webp"
        assert preserved_ship.seed_status == "overridden"

        restored_ship = restore_ship_seed(db, ship.id)
        assert restored_ship.speed_knots == 16.9
        assert restored_ship.image_url is None
        assert restored_ship.seed_status == "seeded"


def test_custom_master_data_is_not_adopted_or_overwritten_by_seeding() -> None:
    with _seeded_db() as db:
        category = db.scalar(
            select(BuildItemOption.category_id).where(BuildItemOption.name == "Copper Plating")
        )
        assert category is not None
        custom = create_option(
            db,
            MasterDataOptionCreate(
                category_id=category,
                name="Fleet Test Plating",
                source="fleet admin",
                notes="Intentionally local catalog entry",
                image_url="/uploads/fleet-test-plating.webp",
                option_kind="upgrade",
                weapon_class=None,
                weapon_caliber_inches=None,
                stat_effects={"armor_pct": 7},
                allowed_slot_types=[],
                sort_order=9990,
                is_active=True,
            ),
        )
        assert custom.seed_status == "custom"
        row = db.get(BuildItemOption, custom.id)
        assert row is not None
        assert row.seed_revision == CUSTOM_MASTER_DATA_REVISION

        SeedManager(db).seed_build_options()

        preserved = db.get(BuildItemOption, custom.id)
        assert preserved is not None
        assert preserved.name == "Fleet Test Plating"
        assert preserved.stat_effects == {"armor_pct": 7.0}
        assert preserved.seed_key is None
        assert preserved.seed_revision == CUSTOM_MASTER_DATA_REVISION


def test_full_seed_is_idempotent_and_never_creates_user_content() -> None:
    with _seeded_db() as db:
        before = (
            int(db.scalar(select(func.count(Ship.id))) or 0),
            int(db.scalar(select(func.count(BuildItemOption.id))) or 0),
        )
        SeedManager(db).run()
        after = (
            int(db.scalar(select(func.count(Ship.id))) or 0),
            int(db.scalar(select(func.count(BuildItemOption.id))) or 0),
        )
        assert after == before
        assert int(db.scalar(select(func.count(Build.id))) or 0) == 0
        assert int(db.scalar(select(func.count(Guide.id))) or 0) == 0


def test_master_data_routes_require_admin() -> None:
    with TestClient(app) as client:
        assert client.get("/api/admin/master-data/overview").status_code == 401
        with SessionLocal() as db:
            create_user(
                db,
                username="master-data-moderator",
                password="MasterDataModerator123!",
                display_name="Master Data Moderator",
                role=ROLE_MODERATOR,
            )
            create_user(
                db,
                username="master-data-admin",
                password="MasterDataAdmin123!",
                display_name="Master Data Admin",
                role=ROLE_ADMIN,
            )

        assert client.post(
            "/api/auth/login",
            json={"username": "master-data-moderator", "password": "MasterDataModerator123!"},
        ).status_code == 200
        assert client.get("/api/admin/master-data/overview").status_code == 403
        assert client.post("/api/auth/logout").status_code == 204

        assert client.post(
            "/api/auth/login",
            json={"username": "master-data-admin", "password": "MasterDataAdmin123!"},
        ).status_code == 200
        response = client.get("/api/admin/master-data/overview")
        assert response.status_code == 200
        assert set(response.json()) == {
            "category_count", "option_count", "ship_count", "overridden_count", "inactive_count"
        }


def test_ship_specific_upgrade_effects_overlay_global_values_and_restore_cleanly() -> None:
    from app.modules.builds.schemas.build_create import BuildCreate
    from app.modules.builds.services.build_option_service import list_build_options
    from app.modules.builds.services.build_service import create_build

    with _seeded_db() as db:
        ship = db.scalar(select(Ship).where(Ship.name == "Firestorm"))
        option = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Lightweight Hull"))
        assert ship is not None and option is not None
        current = next(row for row in list_ships(db, search="Firestorm") if row.id == ship.id)
        payload = current.model_dump(exclude={
            "id", "weapon_layout", "seed_key", "seed_revision", "is_seed_overridden",
            "seed_status", "created_at", "updated_at",
        })
        payload["upgrade_effect_overrides"] = [
            {"option_id": option.id, "stat_effects": {"speed_pct": 12}}
        ]
        updated = update_ship(db, ship.id, MasterDataShipUpdate(**payload))
        assert updated.upgrade_effect_overrides[0].base_stat_effects["speed_pct"] == 4
        assert updated.upgrade_effect_overrides[0].effective_stat_effects["speed_pct"] == 12
        assert option.stat_effects["speed_pct"] == 4

        catalog = list_build_options(db, ship.id)
        lightweight = next(row for row in catalog.options["upgrade"] if row.name == "Lightweight Hull")
        assert lightweight.stat_effects["speed_pct"] == 12
        assert lightweight.base_stat_effects["speed_pct"] == 4
        assert lightweight.is_ship_specific is True

        build = create_build(
            db,
            BuildCreate(
                build_name="Ship-specific lightweight hull",
                ship_id=ship.id,
                sailors=ship.sailor_minimum,
                upgrade_1="Lightweight Hull",
            ),
        )
        assert build.ship_stats["upgrade_effects"]["speed_pct"] == 12

        restored = restore_ship_seed(db, ship.id)
        assert restored.upgrade_effect_overrides == []
        catalog = list_build_options(db, ship.id)
        lightweight = next(row for row in catalog.options["upgrade"] if row.name == "Lightweight Hull")
        assert lightweight.stat_effects["speed_pct"] == 4
        assert lightweight.is_ship_specific is False
