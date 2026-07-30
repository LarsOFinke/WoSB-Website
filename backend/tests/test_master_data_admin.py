from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.audit_log import AuditLog
from app.modules.admin.schemas.master_data import (
    MasterDataCategoryUpdate,
    MasterDataOptionCreate,
    MasterDataOptionUpdate,
    MasterDataShipCreate,
    MasterDataShipUpdate,
)
from app.modules.admin.services.master_data_service import (
    create_option,
    create_ship,
    list_options,
    list_ships,
    restore_all_seed_defaults,
    restore_option_seed,
    restore_ship_seed,
    update_category,
    update_option,
    update_ship,
)
from app.modules.builds.models.build import Build
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.registry import register_all_models
from app.modules.guides.models.guide import Guide
from app.modules.ships.models.ship import Ship
from app.bootstrap.catalog_sync import CUSTOM_MASTER_DATA_REVISION
from app.bootstrap.manager import SeedManager
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
        assert restored.image_url == "/build-assets/options/upgrades/copper-plating.png"
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
        assert restored_ship.speed_knots == 11.3
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


def test_bulk_restore_resets_all_repository_master_data_and_preserves_custom_records() -> None:
    with _seeded_db() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "upgrade"))
        option = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Copper Plating"))
        ship = db.scalar(select(Ship).where(Ship.name == "Firestorm"))
        assert category is not None and option is not None and ship is not None

        original_category_label = category.label
        original_option_effects = option.stat_effects
        original_ship_speed = ship.speed_knots

        update_category(
            db,
            category.id,
            MasterDataCategoryUpdate(
                label="Locally modified upgrades",
                sort_order=category.sort_order,
                is_active=False,
            ),
        )
        update_option(
            db,
            option.id,
            MasterDataOptionUpdate(
                category_id=option.category_id,
                name=option.name,
                source="local override",
                notes=option.notes,
                image_url=option.image_url,
                option_kind=option.option_kind,
                weapon_class=option.weapon_class_code,
                weapon_caliber_inches=option.weapon_caliber_inches,
                stat_effects={"water_fire_protection_pct": 99},
                allowed_slot_types=option.allowed_slots,
                sort_order=option.sort_order,
                is_active=False,
            ),
        )
        current_ship = next(row for row in list_ships(db, search="Firestorm") if row.id == ship.id)
        update_ship(
            db,
            ship.id,
            MasterDataShipUpdate(
                **{
                    **current_ship.model_dump(exclude={
                        "id", "weapon_layout", "seed_key", "seed_revision",
                        "is_seed_overridden", "seed_status", "created_at", "updated_at",
                    }),
                    "speed_knots": 42,
                    "is_active": False,
                }
            ),
        )
        custom = create_option(
            db,
            MasterDataOptionCreate(
                category_id=category.id,
                name="Local Fleet Ammunition",
                source="fleet admin",
                notes="Must survive repository restore",
                image_url=None,
                option_kind="ammo",
                weapon_class=None,
                weapon_caliber_inches=None,
                stat_effects={"crew_damage_pct": 3},
                allowed_slot_types=[],
                sort_order=9999,
                is_active=True,
            ),
        )

        summary = restore_all_seed_defaults(db)

        assert summary.categories > 1
        assert summary.options > 1
        assert summary.ships > 1
        assert summary.total == summary.categories + summary.options + summary.ships
        assert summary.overrides_discarded == 3
        assert summary.custom_records_preserved is True

        restored_category = db.get(BuildItemCategory, category.id)
        restored_option = db.get(BuildItemOption, option.id)
        restored_ship = db.get(Ship, ship.id)
        preserved_custom = db.get(BuildItemOption, custom.id)
        assert restored_category is not None and restored_category.label == original_category_label
        assert restored_category.is_active is True
        assert restored_category.is_seed_overridden is False
        assert restored_option is not None and restored_option.stat_effects == original_option_effects
        assert restored_option.is_active is True
        assert restored_option.is_seed_overridden is False
        assert restored_ship is not None and restored_ship.speed_knots == original_ship_speed
        assert restored_ship.is_active is True
        assert restored_ship.is_seed_overridden is False
        assert preserved_custom is not None
        assert preserved_custom.name == "Local Fleet Ammunition"
        assert preserved_custom.seed_key is None
        assert preserved_custom.stat_effects == {"crew_damage_pct": 3.0}


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
        assert client.post("/api/admin/master-data/restore-seed-defaults").status_code == 403
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
        restore_response = client.post("/api/admin/master-data/restore-seed-defaults")
        assert restore_response.status_code == 200
        assert set(restore_response.json()) == {
            "categories", "options", "ships", "total", "overrides_discarded",
            "custom_records_preserved"
        }
        assert restore_response.json()["custom_records_preserved"] is True
        with SessionLocal() as db:
            audit = db.scalar(
                select(AuditLog)
                .where(
                    AuditLog.entity_type == "master_data",
                    AuditLog.action == "restore_seed_defaults",
                )
                .order_by(AuditLog.id.desc())
            )
            assert audit is not None
            assert audit.actor_username == "master-data-admin"


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
        restored_effects = {
            row.option_name: row.effective_stat_effects
            for row in restored.upgrade_effect_overrides
        }
        assert restored_effects["Reinforced Cannons"] == {
            "bow_stern_weapon_damage_pct": 35,
        }
        assert restored_effects["Reinforced Masts"] == {
            "speed_knots": 0.4,
            "sail_efficiency": 0.8,
        }
        assert "Lightweight Hull" not in restored_effects
        catalog = list_build_options(db, ship.id)
        lightweight = next(row for row in catalog.options["upgrade"] if row.name == "Lightweight Hull")
        assert lightweight.stat_effects["speed_pct"] == 4
        assert lightweight.is_ship_specific is False


def test_new_custom_ships_receive_rate_weapon_class_defaults() -> None:
    with _seeded_db() as db:
        def payload(rate: int, name: str, explicit_class: str | None = None):
            return MasterDataShipCreate(
                name=name,
                rate=rate,
                ship_type="Test frigate",
                durability=100,
                speed_min_knots=5,
                speed_knots=8,
                maneuverability=50,
                armor=2,
                hold_capacity=100,
                crew_capacity=50,
                sailor_minimum=10,
                displacement_tons=100,
                source="manual test",
                weapon_mounts=[
                    {
                        "slot_type": code,
                        "capacity": 4 if code in {"weapon_port", "weapon_starboard"} else 0,
                        "special_weapon_capacity": 0,
                        "max_weapon_class": (
                            explicit_class
                            if code in {"weapon_port", "weapon_starboard"}
                            else None
                        ),
                        "max_caliber_inches": None,
                    }
                    for code in (
                        "weapon_front",
                        "weapon_rear",
                        "weapon_port",
                        "weapon_starboard",
                        "weapon_mortar",
                        "weapon_special",
                    )
                ],
            )

        ships_by_rate = {
            rate: create_ship(db, payload(rate, f"Automatic rate {rate} test"))
            for rate in range(1, 8)
        }
        exception_ship = create_ship(
            db, payload(6, "Explicit weapon exception", explicit_class="heavy")
        )

        def broadside_classes(ship):
            return {
                mount.max_weapon_class
                for mount in ship.weapon_mounts
                if mount.slot_type in {"weapon_port", "weapon_starboard"}
            }

        expected_by_rate = {
            1: "heavy",
            2: "heavy",
            3: "medium",
            4: "medium",
            5: "light",
            6: "light",
            7: "light",
        }
        assert {
            rate: broadside_classes(ship)
            for rate, ship in ships_by_rate.items()
        } == {rate: {weapon_class} for rate, weapon_class in expected_by_rate.items()}
        assert broadside_classes(exception_ship) == {"heavy"}
        assert all(
            mount.max_weapon_class is None
            for mount in ships_by_rate[6].weapon_mounts
            if mount.slot_type in {"weapon_mortar", "weapon_special"}
        )
