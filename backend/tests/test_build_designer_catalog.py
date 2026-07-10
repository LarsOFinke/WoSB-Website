from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_service import BuildValidationError, create_build
from app.modules.ships.models.ship import Ship
from app.seeds.ships import SHIP_SEED_DATA
from app.seeds.weapons import WEAPON_OPTIONS
from app.seeds.weapon_mounts import parse_weapon_layout


EXPECTED_WEAPON_LAYOUTS = {
    "Firestorm": "1-28-12",
    "Ingermanland": "4-32-0",
    "Poltava": "4-23-0",
    "Surprise": "2-18-0",
    "Axel Thorsen": "0-7-3",
    "La Creole": "0-12-4",
    "Le Cerf": "0-9-0",
    "Savannah": "0-9-0",
    "Pickle": "0-6-0",
    "De Zeven Provincien": "4-42-4",
    "Sovereign": "8-38-4 + mortar 7in x2",
    "Victory": "4-49-4",
    "Neptuno": "4-36-4",
    "Sans Pareil": "2-38-4",
    "Anson": "2-30-4",
    "Le Saint Louis": "6-26-6",
    "Essex": "2-21-2",
    "Red Arrow": "6-15-0 + mortar 7in x1",
    "Black Wind": "2-16-2",
    "Kwee Song": "10-10-0",
    "La Salamandre": "0-10-2",
    "Shunsen": "0-10-0",
    "Horizont": "0-8-2",
    "La Couronne": "0-28-8",
    "La Sirene": "0-32-4",
    "Mordaunt": "0-26-4",
    "Prins Willem": "4-26-6",
    "Falmouth": "0-18-4",
    "Flying Cloud": "0-16-0",
    "Friedrich Wilhelm": "4-21-4",
    "Russia": "0-14-2",
    "Mercury": "0-9-2",
    "Friede": "0-7-2",
    "12 Apostolov": "0-59-0",
    "Santisima Trinidad": "0-63-4",
    "Redoutable": "0-43-0",
    "St. Pavel": "0-44-2",
    "Vasa": "2-31-4",
    "Azov": "8-35-8",
    "Bellona": "0-35-0",
    "Constitution": "0-26-0",
    "San Martin": "0-20-0",
    "Phoenix": "0-12-0",
    "La Royale": "6-18-0 + mortar 11in x3",
    "Adventure": "0-19-4 + mortar 10in x2",
    "Kobukson": "0-15-0 + mortar 9in x4",
    "Shen": "1-22-0 + mortar 11in x2",
    "Sparrow": "0-4-0 + mortar 8in x3",
    "Eagle": "0-8-4",
    "Le Requin": "0-12-2 + mortar 7in x1",
    "Golden Apostle": "0-7-0 + mortar 6in x1",
    "Polacca": "0-7-0 + mortar 6in x1",
    "Huracan": "2-85-0",
    "Octopus": "0-37-8",
    "Deadfish": "1-25-8",
    "Devourer": "8-11-12",
    "Black Prince": "2-15-2",
    "Balloon": "0-4-0",
}


def test_all_ship_weapon_layouts_match_audited_catalog() -> None:
    actual = {row["name"]: row["weapon_layout"] for row in SHIP_SEED_DATA}
    assert actual == EXPECTED_WEAPON_LAYOUTS
    zeven = next(row for row in SHIP_SEED_DATA if row["name"] == "De Zeven Provincien")
    mounts = {row["slot_type"]: row for row in parse_weapon_layout(zeven["weapon_layout"], rate=zeven["rate"])}
    assert mounts["weapon_front"]["capacity"] == 4
    assert mounts["weapon_port"]["capacity"] == 42
    assert mounts["weapon_rear"]["capacity"] == 4


def test_duplicate_upgrades_are_rejected_server_side() -> None:
    with SessionLocal() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "upgrade"))
        if category is None:
            category = BuildItemCategory(key="upgrade", label="Upgrades", sort_order=10, is_active=True)
            db.add(category)
            db.flush()
        option = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Duplicate Test Upgrade",
            )
        )
        if option is None:
            option = BuildItemOption(
                category_id=category.id,
                name="Duplicate Test Upgrade",
                sort_order=10,
                is_active=True,
            )
            db.add(option)
        ship = db.scalar(select(Ship).where(Ship.name == "Duplicate Upgrade Test Ship"))
        if ship is None:
            ship = Ship(
                name="Duplicate Upgrade Test Ship",
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
            )
            db.add(ship)
        db.commit()
        try:
            create_build(
                db,
                BuildCreate(
                    build_name="Duplicate upgrades",
                    ship_id=ship.id,
                    upgrade_1="Duplicate Test Upgrade",
                    upgrade_2="Duplicate Test Upgrade",
                ),
            )
        except BuildValidationError as exc:
            assert "each upgrade can only be selected once" in str(exc)
        else:
            raise AssertionError("Duplicate upgrades must be rejected.")


def test_weapon_catalog_uses_dedicated_ship_arcs() -> None:
    expected = {
        "cannon": {"weapon_port", "weapon_starboard"},
        "bow_stern": {"weapon_front", "weapon_rear"},
        "mortar": {"weapon_mortar"},
    }
    assert WEAPON_OPTIONS
    for row in WEAPON_OPTIONS:
        slots = {slot.strip() for slot in str(row["allowed_slot_types"]).split(",") if slot.strip()}
        assert slots == expected[row["option_kind"]], row["name"]
