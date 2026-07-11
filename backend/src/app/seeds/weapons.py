"""Audited weapon catalog with normalized slot and size-class metadata."""

CANNON_SLOT_TYPES = "weapon_port,weapon_starboard"
BOW_STERN_SLOT_TYPES = "weapon_front,weapon_rear"
MORTAR_SLOT_TYPES = "weapon_mortar"
SPECIAL_WEAPON_SLOT_TYPES = "weapon_special"
SOURCE = "WoSB wiki Basic Weapons audit 2026-07"


def cannon(name: str, weapon_class: str, *, source: str = SOURCE) -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "cannon",
        "allowed_slot_types": CANNON_SLOT_TYPES,
        "weapon_class": weapon_class,
    }


def bow_stern(name: str, weapon_class: str, *, source: str = SOURCE) -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "bow_stern",
        "allowed_slot_types": BOW_STERN_SLOT_TYPES,
        "weapon_class": weapon_class,
    }


def mortar(
    name: str,
    caliber: float | int | None = None,
    *,
    source: str = SOURCE,
) -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "mortar",
        "allowed_slot_types": MORTAR_SLOT_TYPES,
        "weapon_class": None,
        "weapon_caliber_inches": caliber,
    }


def special_weapon(name: str, *, source: str = SOURCE) -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "special_weapon",
        "allowed_slot_types": SPECIAL_WEAPON_SLOT_TYPES,
        "weapon_class": None,
        "weapon_caliber_inches": None,
    }


def mortar_launcher(name: str, *, source: str = SOURCE) -> dict[str, object]:
    return {
        "category": "weapon",
        "name": name,
        "source": source,
        "option_kind": "mortar_launcher",
        "allowed_slot_types": MORTAR_SLOT_TYPES,
        "weapon_class": None,
        "weapon_caliber_inches": None,
    }


WEAPON_OPTIONS = [
    # Light broadside weapons
    cannon("6-pdr Culverin", "light"),
    cannon("6-pdr Rusty Cannon", "light"),
    cannon("8-pdr Cannon", "light"),
    cannon("8-pdr Culverin", "light"),
    cannon("12-pdr Carronade", "light"),
    # Medium broadside weapons
    cannon("16-pdr Cannon", "medium"),
    cannon("16-pdr Carronade", "medium"),
    cannon("16-pdr Culverin", "medium"),
    cannon("18-pdr Cannon", "medium"),
    cannon("18-pdr Long Cannon", "medium"),
    cannon("20-pdr Admiral", "medium"),
    cannon("22-pdr Scorcher", "medium"),
    cannon("24-pdr Carronade", "medium"),
    cannon("28-pdr Carronade", "medium"),
    # Heavy broadside weapons
    cannon("32-pdr Cannon", "heavy"),
    cannon("32-pdr Long Cannon", "heavy"),
    cannon("32-pdr Stormbringer", "heavy"),
    cannon("36-pdr Inrog", "heavy"),
    cannon("38-pdr Jericho", "heavy"),
    cannon("42-pdr Carronade", "heavy"),
    cannon("48-pdr Colossus", "heavy"),
    # Light bow/stern launchers
    special_weapon("Alchemical Fire"),
    mortar_launcher("Barrel Launcher"),
    bow_stern("Twin 6-pdr", "light"),
    bow_stern("Triple 10-pdr", "light"),
    # Medium bow/stern bombards
    bow_stern("Basilisk", "medium"),
    special_weapon("Imperial Bombard"),
    bow_stern("Onager", "medium"),
    bow_stern("Twin 14-pdr", "medium"),
    bow_stern("Triple 16-pdr", "medium"),
    # Heavy bow/stern bombards
    bow_stern("Gilgamesh", "heavy"),
    bow_stern("Mjolnir", "heavy"),
    bow_stern("Poseidon", "heavy"),
    bow_stern("Twin 20-pdr", "heavy"),
    bow_stern("Zeus", "heavy"),
    # Dedicated mortar slot weapons
    mortar("6-inch Mortar", 6),
    mortar("7-inch Mortar", 7),
    mortar("8-inch Mortar", 8),
    mortar("9-inch Mortar", 9),
    mortar("10-inch Mortar", 10),
    mortar("11-inch Mortar", 11),
    mortar("Heavy Mortar", 11),
]
