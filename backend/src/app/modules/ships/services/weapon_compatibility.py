from __future__ import annotations

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.weapon_mount import ShipWeaponMount


def is_weapon_compatible(option: BuildItemOption, mount: ShipWeaponMount) -> bool:
    """Return whether a catalog weapon fits one normalized ship mount.

    Slot taxonomy is authoritative first. Regular weapons are constrained by
    Light/Medium/Heavy rank; mortars use their dedicated caliber limit.
    """

    if mount.capacity <= 0 or mount.slot_type.code not in option.allowed_slots:
        return False

    if mount.slot_type.code == "weapon_mortar":
        if option.option_kind != "mortar":
            return False
        if mount.max_caliber_inches is None:
            return False
        return option.weapon_caliber_inches is None or option.weapon_caliber_inches <= mount.max_caliber_inches

    if option.option_kind == "mortar":
        return False
    if option.weapon_class is None or mount.max_weapon_class is None:
        return False
    return option.weapon_class.rank <= mount.max_weapon_class.rank
