BUILD_TYPE_VALUES = {"balanced", "gunnery", "boarding", "defensive"}

BUILD_CLASSIFICATION_VALUES = {
    "port_battle",
    "pve_solo",
    "pve_group",
    "pve_instanced",
    "pvp_solo",
    "pvp_group",
    "pvp_instanced",
    "trading",
    "fast",
    "combat",
    "heavy",
    "transport",
    "siege",
    "imperial",
}

MAX_BUILD_CLASSIFICATIONS = 6
WEAPON_ARC_KEYS = ("front", "rear", "port", "starboard")
WEAPON_SLOT_FIELDS = tuple(f"{arc}_weapon_slots" for arc in WEAPON_ARC_KEYS)
WEAPON_LOADOUT_FIELDS = (*WEAPON_SLOT_FIELDS, "mortar_weapon_slots", "special_weapon_slots")
