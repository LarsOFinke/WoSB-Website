import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_option_service import list_build_options
from app.modules.builds.services.build_service import BuildValidationError, create_build
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship
from app.modules.ships.services.weapon_compatibility import is_weapon_compatible
from app.bootstrap.manager import SeedManager


def _catalog(db: Session, ship: Ship) -> dict[str, set[str]]:
    rows = list_build_options(db, ship_id=ship.id).options["weapon"]
    by_slot: dict[str, set[str]] = {}
    for row in rows:
        for slot in row.allowed_slot_types:
            by_slot.setdefault(slot, set()).add(row.name)
    return by_slot


def test_weapon_dropdown_uses_class_for_broadsides_and_slot_type_for_positional_weapons() -> None:
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
        zeus = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Zeus"))
        assert all(
            (
                russia,
                essex,
                poltava,
                victory,
                cannon_8,
                cannon_16,
                cannon_32,
                twin_6,
                twin_14,
                zeus,
            )
        )

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
        russia_rear = russia._mount("weapon_rear")
        assert russia_port and russia_rear
        assert is_weapon_compatible(cannon_8, russia_port)
        assert not is_weapon_compatible(cannon_16, russia_port)
        assert is_weapon_compatible(twin_6, russia_rear)
        assert is_weapon_compatible(twin_14, russia_rear)
        assert is_weapon_compatible(zeus, russia_rear)
        assert not is_weapon_compatible(twin_6, russia_port)
        assert not is_weapon_compatible(zeus, russia_port)


def test_weapon_families_use_normalized_class_or_slot_compatibility() -> None:
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
            elif option.option_kind == "cannon":
                assert option.weapon_class_code in {"light", "medium", "heavy"}
                assert set(option.allowed_slots) == {"weapon_port", "weapon_starboard"}
            else:
                assert option.option_kind in {
                    "bow_stern",
                    "mortar_launcher",
                    "special_weapon",
                }
                assert option.weapon_class is None
                assert option.weapon_caliber_inches is None


def test_special_weapons_follow_audited_positional_mounts_and_launchers_use_mortar_slots() -> None:
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
        octopus = db.scalar(select(Ship).where(Ship.name == "Octopus"))
        axel = db.scalar(select(Ship).where(Ship.name == "Axel Thorsen"))
        victory = db.scalar(select(Ship).where(Ship.name == "Victory"))
        sovereign = db.scalar(select(Ship).where(Ship.name == "Sovereign"))
        assert huracan and deadfish and octopus and axel and victory and sovereign

        for special_ship, capacity in ((huracan, 2), (deadfish, 1)):
            catalog = _catalog(db, special_ship)
            assert special_ship.special_weapon_capacity == capacity
            assert {"Alchemical Fire", "Imperial Bombard"} <= catalog["weapon_front"]
            assert "weapon_special" not in catalog
            assert "Imperial Bombard" not in catalog.get("weapon_rear", set())

        octopus_catalog = _catalog(db, octopus)
        assert {"Alchemical Fire", "Imperial Bombard"} <= octopus_catalog["weapon_rear"]
        assert "Alchemical Fire" not in octopus_catalog.get("weapon_front", set())
        assert "weapon_special" not in octopus_catalog

        axel_catalog = _catalog(db, axel)
        assert {"Alchemical Fire", "Imperial Bombard"} <= axel_catalog["weapon_special"]
        assert "Alchemical Fire" not in axel_catalog.get("weapon_front", set())
        assert "Imperial Bombard" not in axel_catalog.get("weapon_rear", set())

        regular_catalog = _catalog(db, victory)
        assert "Alchemical Fire" not in regular_catalog.get("weapon_front", set())
        assert "Imperial Bombard" not in regular_catalog.get("weapon_front", set())
        assert "weapon_special" not in regular_catalog

        mortar_catalog = _catalog(db, sovereign)
        assert "Barrel Launcher" in mortar_catalog["weapon_mortar"]
        assert "Barrel Launcher" not in mortar_catalog.get("weapon_front", set())
        assert "Barrel Launcher" not in mortar_catalog.get("weapon_rear", set())


def test_special_weapon_quantity_is_limited_inside_a_larger_positional_mount() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()

        octopus = db.scalar(select(Ship).where(Ship.name == "Octopus"))
        assert octopus is not None
        assert octopus.rear_weapon_capacity == 8
        assert octopus.rear_special_weapon_capacity == 1

        accepted = create_build(
            db,
            BuildCreate(
                build_name="One audited stern special weapon",
                ship_id=octopus.id,
                sailors=octopus.sailor_minimum,
                rear_weapon_slots=[{"item": "Imperial Bombard", "quantity": 1}],
            ),
        )
        assert accepted.rear_weapon_slots == [{"item": "Imperial Bombard", "quantity": 1}]

        with pytest.raises(BuildValidationError, match="special capacity \\(1\\)"):
            create_build(
                db,
                BuildCreate(
                    build_name="Too many stern special weapons",
                    ship_id=octopus.id,
                    sailors=octopus.sailor_minimum,
                    rear_weapon_slots=[{"item": "Imperial Bombard", "quantity": 2}],
                ),
            )


def test_mortar_modification_exchanges_broadsides_for_mortar_capacity() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()

        black_wind = db.scalar(select(Ship).where(Ship.name == "Black Wind"))
        assert black_wind is not None
        assert black_wind.mortar_modification is not None
        assert black_wind.mortar_weapon_capacity == 0
        assert "7-inch Mortar" in _catalog(db, black_wind)["weapon_mortar"]

        with pytest.raises(BuildValidationError, match="capacity \\(0\\)"):
            create_build(
                db,
                BuildCreate(
                    build_name="Modification missing",
                    ship_id=black_wind.id,
                    sailors=black_wind.sailor_minimum,
                    mortar_weapon_slots=[{"item": "7-inch Mortar", "quantity": 1}],
                ),
            )

        accepted = create_build(
            db,
            BuildCreate(
                build_name="Permanent mortar conversion",
                ship_id=black_wind.id,
                mortar_modification_installed=True,
                sailors=black_wind.sailor_minimum,
                port_weapon_slots=[{"item": "8-pdr Cannon", "quantity": 11}],
                starboard_weapon_slots=[{"item": "8-pdr Cannon", "quantity": 11}],
                mortar_weapon_slots=[{"item": "7-inch Mortar", "quantity": 1}],
            ),
        )
        assert accepted.ship_stats["weapon_capacity"]["port"] == 11
        assert accepted.ship_stats["weapon_capacity"]["starboard"] == 11
        assert accepted.ship_stats["weapon_capacity"]["mortar"] == 1
        assert accepted.ship_stats["effective_crew_capacity"] == 93
        assert accepted.ship_stats["mortar_modification_effects"] == {
            "durability": -180,
            "maneuverability": 15,
            "crew_capacity": -23,
        }

        with pytest.raises(BuildValidationError, match="capacity \\(11\\)"):
            create_build(
                db,
                BuildCreate(
                    build_name="Too many broadside guns",
                    ship_id=black_wind.id,
                    mortar_modification_installed=True,
                    sailors=black_wind.sailor_minimum,
                    port_weapon_slots=[{"item": "8-pdr Cannon", "quantity": 12}],
                ),
            )

        with pytest.raises(BuildValidationError, match="caliber limit \\(7"):
            create_build(
                db,
                BuildCreate(
                    build_name="Mortar too large",
                    ship_id=black_wind.id,
                    mortar_modification_installed=True,
                    sailors=black_wind.sailor_minimum,
                    mortar_weapon_slots=[{"item": "8-inch Mortar", "quantity": 1}],
                ),
            )


def test_bow_stern_weapons_are_available_to_every_compatible_ship_mount() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()

        positional_weapons = db.scalars(
            select(BuildItemOption).where(
                BuildItemOption.option_kind == "bow_stern",
                BuildItemOption.is_active.is_(True),
            )
        ).unique().all()
        positional_names = {option.name for option in positional_weapons}
        assert {"Zeus", "Basilisk", "Poseidon"} <= positional_names
        assert all(option.weapon_class is None for option in positional_weapons)
        assert all(
            set(option.allowed_slots) == {"weapon_front", "weapon_rear"}
            for option in positional_weapons
        )

        ships = db.scalars(select(Ship).where(Ship.is_active.is_(True))).unique().all()
        assert ships
        for ship in ships:
            catalog = _catalog(db, ship)
            for slot_code in ("weapon_front", "weapon_rear"):
                mount = ship._mount(slot_code)
                assert mount is not None
                available = catalog.get(slot_code, set())
                if mount.capacity > 0:
                    assert positional_names <= available, (ship.name, slot_code)
                else:
                    assert positional_names.isdisjoint(available), (ship.name, slot_code)
            for slot_code in (
                "weapon_port",
                "weapon_starboard",
                "weapon_mortar",
                "weapon_special",
            ):
                assert positional_names.isdisjoint(catalog.get(slot_code, set())), (
                    ship.name,
                    slot_code,
                )

        russia = db.scalar(select(Ship).where(Ship.name == "Russia"))
        eagle = db.scalar(select(Ship).where(Ship.name == "Eagle"))
        assert russia and eagle

        russia_build = create_build(
            db,
            BuildCreate(
                build_name="Russia positional Zeus",
                ship_id=russia.id,
                sailors=russia.sailor_minimum,
                rear_weapon_slots=[{"item": "Zeus", "quantity": 1}],
            ),
        )
        assert russia_build.rear_weapon_slots == [{"item": "Zeus", "quantity": 1}]

        eagle_build = create_build(
            db,
            BuildCreate(
                build_name="Eagle standard stern weapons",
                ship_id=eagle.id,
                sailors=eagle.sailor_minimum,
                rear_weapon_slots=[
                    {"item": "Basilisk", "quantity": 1},
                    {"item": "Poseidon", "quantity": 1},
                ],
            ),
        )
        assert eagle_build.rear_weapon_slots == [
            {"item": "Basilisk", "quantity": 1},
            {"item": "Poseidon", "quantity": 1},
        ]

