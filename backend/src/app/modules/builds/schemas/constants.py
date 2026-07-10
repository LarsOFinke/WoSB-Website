BUILD_TYPE_VALUES = {"balanced", "gunnery", "boarding", "defensive"}
WEAPON_ARC_KEYS = ("front", "rear", "port", "starboard")
WEAPON_SLOT_FIELDS = tuple(f"{arc}_weapon_slots" for arc in WEAPON_ARC_KEYS)
WEAPON_LOADOUT_FIELDS = (*WEAPON_SLOT_FIELDS, "mortar_weapon_slots")
