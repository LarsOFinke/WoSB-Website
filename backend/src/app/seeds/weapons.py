"""Weapon option seeds with Build Designer slot metadata.

The public WoSB weapon overview groups weapons into cannons/long cannons,
carronades, bombards, mortars and special weapons. We keep that taxonomy in the
catalog so the Build Designer can prevent invalid ship+slot combinations without
hard-coding names in frontend code.
"""

CANNON_SLOT_TYPES = "weapon_front,weapon_rear,weapon_port,weapon_starboard"
BOW_STERN_SLOT_TYPES = "weapon_front,weapon_rear"
MORTAR_SLOT_TYPES = "weapon_mortar"


def cannon(name: str, *, source: str = "wiki") -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "cannon",
        "allowed_slot_types": CANNON_SLOT_TYPES,
    }


def bow_stern(name: str, *, source: str = "wiki") -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "bow_stern",
        "allowed_slot_types": BOW_STERN_SLOT_TYPES,
    }


def mortar(name: str, caliber: float | int | None = None, *, source: str = "wiki") -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "mortar",
        "allowed_slot_types": MORTAR_SLOT_TYPES,
        "weapon_caliber_inches": caliber,
    }


WEAPON_OPTIONS = [
    # Cannons / long cannons / carronades
    cannon("6-pdr Culverin"),
    cannon("6-pdr Rusty Cannon"),
    cannon("8-pdr Cannon"),
    cannon("8-pdr Culverin"),
    cannon("12-pdr Carronade"),
    cannon("16-pdr Cannon"),
    cannon("16-pdr Carronade"),
    cannon("16-pdr Culverin"),
    cannon("18-pdr Cannon"),
    cannon("18-pdr Long Cannon"),
    cannon("20-pdr Admiral"),
    cannon("22-pdr Scorcher"),
    cannon("24-pdr Carronade"),
    cannon("28-pdr Carronade"),
    cannon("32-pdr Cannon"),
    cannon("32-pdr Long Cannon"),
    cannon("32-pdr Stormbringer"),
    cannon("36-pdr Inrog"),
    cannon("38-pdr Jericho"),
    cannon("42-pdr Carronade"),
    cannon("48-pdr Colossus"),
    # Bow/stern bombards and special launchers
    bow_stern("Alchemical Fire"),
    bow_stern("Barrel Launcher"),
    bow_stern("Basilisk"),
    bow_stern("Gilgamesh"),
    bow_stern("Imperial Bombard"),
    bow_stern("Mjolnir"),
    bow_stern("Onager"),
    bow_stern("Poseidon"),
    bow_stern("Triple 10-pdr"),
    bow_stern("Triple 16-pdr"),
    bow_stern("Twin 6-pdr"),
    bow_stern("Twin 14-pdr"),
    bow_stern("Twin 20-pdr"),
    bow_stern("Zeus"),
    # Dedicated mortar slot weapons
    mortar("6-inch Mortar", 6),
    mortar("7-inch Mortar", 7),
    mortar("8-inch Mortar", 8),
    mortar("9-inch Mortar", 9),
    mortar("10-inch Mortar", 10),
    mortar("11-inch Mortar", 11),
    mortar("Heavy Mortar", 11),
]
