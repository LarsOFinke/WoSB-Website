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
        cannon_16 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "16-pdr Cannon"))
        cannon_32 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "32-pdr Cannon"))
        twin_14 = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Twin 14-pdr"))
        assert russia and essex and poltava and victory and cannon_16 and cannon_32 and twin_14

        # Fifth- and fourth-rate ships use Medium mounts: medium weapons fit,
        # Heavy weapons do not. Third-rate and larger ships accept Heavy.
        for medium_ship in (russia, essex):
            catalog = _catalog(db, medium_ship)
            assert "16-pdr Cannon" in catalog["weapon_port"]
            assert "32-pdr Cannon" not in catalog["weapon_port"]

        for heavy_ship in (poltava, victory):
            catalog = _catalog(db, heavy_ship)
            assert "32-pdr Cannon" in catalog["weapon_port"]

        # Bow/stern weapons never leak into broadside choices.
        victory_catalog = _catalog(db, victory)
        assert "Twin 14-pdr" not in victory_catalog["weapon_port"]
        assert "Twin 14-pdr" in victory_catalog["weapon_front"]

        russia_port = russia._mount("weapon_port")
        russia_rear = russia._mount("weapon_rear")
        assert russia_port and russia_rear
        assert is_weapon_compatible(cannon_16, russia_port)
        assert not is_weapon_compatible(cannon_32, russia_port)
        assert is_weapon_compatible(twin_14, russia_rear)
        assert not is_weapon_compatible(twin_14, russia_port)


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
            else:
                assert option.weapon_class_code in {"light", "medium", "heavy"}
