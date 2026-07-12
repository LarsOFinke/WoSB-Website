from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.services.build_option_service import list_build_options
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.modules.ships.services.weapon_compatibility import is_weapon_compatible
from app.seeds.manager import SeedManager


def _catalog(db: Session, ship: Ship) -> dict[str, set[str]]:
    rows = list_build_options(db, ship_id=ship.id).options["weapon"]
    by_slot: dict[str, set[str]] = {}
    for row in rows:
        for slot in row.allowed_slot_types:
            by_slot.setdefault(slot, set()).add(row.name)
    return by_slot


def test_weapon_dropdown_is_scoped_to_ship_slot_and_weapon_class() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()

        russia = db.scalar(select(Ship).where(Ship.name == "Russia"))
        essex = db.scalar(select(Ship).where(Ship.name == "Essex"))
        poltava = db.scalar(select(Ship).where(Ship.name == "Poltava"))
        victory = db.scalar(select(Ship).where(Ship.name == "Victory"))
        cannon_8 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "8-pdr Cannon"))
        cannon_16 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "16-pdr Cannon"))
        cannon_32 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "32-pdr Cannon"))
        twin_6 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Twin 6-pdr"))
        twin_14 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Twin 14-pdr"))
        assert all((russia, essex, poltava, victory, cannon_8, cannon_16, cannon_32, twin_6, twin_14))

        # The mount ceiling is audited per ship rather than inferred from rate.
        # Russia uses Light mounts, Essex and Poltava use Medium, Victory accepts Heavy.
        russia_catalog = _catalog(db, russia)
        assert "8-pdr Cannon" in russia_catalog["weapon_port"]
        assert "16-pdr Cannon" not in russia_catalog["weapon_port"]

        for medium_ship in (essex, poltava):
            catalog = _catalog(db, medium_ship)
            assert "16-pdr Cannon" in catalog["weapon_port"]
            assert "32-pdr Cannon" not in catalog["weapon_port"]

        victory_catalog = _catalog(db, victory)
        assert "32-pdr Cannon" in victory_catalog["weapon_port"]

        # Bow/stern weapons never leak into broadside choices.
        assert "Twin 14-pdr" not in victory_catalog["weapon_port"]
        assert "Twin 14-pdr" in victory_catalog["weapon_front"]

        russia_port = russia._mount("weapon_port")
        russia_front = russia._mount("weapon_front")
        assert russia_port and russia_front
        assert is_weapon_compatible(cannon_8, russia_port)
        assert not is_weapon_compatible(cannon_16, russia_port)
        assert is_weapon_compatible(twin_6, russia_front)
        assert not is_weapon_compatible(twin_14, russia_front)
        assert not is_weapon_compatible(twin_6, russia_port)


def test_every_active_regular_weapon_has_a_normalized_size_class() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_build_options()
        weapons = db.scalars(select(BuildItemOption).where(BuildItemOption.is_active.is_(True))).unique().all()
        weapons = [row for row in weapons if row.category.key == "weapon"]
        assert weapons
        for option in weapons:
            if option.option_kind == "mortar":
                assert option.weapon_class is None
                assert option.weapon_caliber_inches is not None
            elif option.option_kind in {"mortar_launcher", "special_weapon"}:
                assert option.weapon_class is None
                assert option.weapon_caliber_inches is None
            else:
                assert option.weapon_class_code in {"light", "medium", "heavy"}


def test_special_and_launcher_weapons_use_only_dedicated_mounts() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()

        huracan = db.scalar(select(Ship).where(Ship.name == "Huracan"))
        deadfish = db.scalar(select(Ship).where(Ship.name == "Deadfish"))
        victory = db.scalar(select(Ship).where(Ship.name == "Victory"))
        sovereign = db.scalar(select(Ship).where(Ship.name == "Sovereign"))
        assert huracan and deadfish and victory and sovereign

        for special_ship, capacity in ((huracan, 2), (deadfish, 1)):
            catalog = _catalog(db, special_ship)
            assert special_ship.special_weapon_capacity == capacity
            assert {"Alchemical Fire", "Imperial Bombard"} <= catalog["weapon_special"]
            assert "Alchemical Fire" not in catalog.get("weapon_front", set())
            assert "Imperial Bombard" not in catalog.get("weapon_rear", set())

        regular_catalog = _catalog(db, victory)
        assert "Alchemical Fire" not in regular_catalog.get("weapon_front", set())
        assert "Imperial Bombard" not in regular_catalog.get("weapon_front", set())
        assert "weapon_special" not in regular_catalog

        mortar_catalog = _catalog(db, sovereign)
        assert "Barrel Launcher" in mortar_catalog["weapon_mortar"]
        assert "Barrel Launcher" not in mortar_catalog.get("weapon_front", set())
        assert "Barrel Launcher" not in mortar_catalog.get("weapon_rear", set())
