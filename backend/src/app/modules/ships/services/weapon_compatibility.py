from __future__ import annotations

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.ships.models.weapon_mount import ShipWeaponMount


def is_weapon_compatible(
    option: BuildItemOption,
    mount: ShipWeaponMount,
    *,
    capacity_override: int | None = None,
    max_caliber_override: int | float | None = None,
) -> bool:
    """Return whether a catalog weapon fits one normalized ship mount.

    Slot taxonomy is authoritative first. Weapons that declare a size class
    also respect the Light/Medium/Heavy ceiling. Positional weapons use their
    normalized slot links, while mortars use the dedicated caliber limit.
    """

    capacity = mount.capacity if capacity_override is None else capacity_override
    if capacity <= 0 or mount.slot_type.code not in option.allowed_slots:
        return False

    if mount.slot_type.code == "weapon_mortar":
        if option.option_kind not in {"mortar", "mortar_launcher"}:
            return False
        if option.option_kind == "mortar_launcher":
            return True
        max_caliber = (
            mount.max_caliber_inches
            if max_caliber_override is None
            else max_caliber_override
        )
        if max_caliber is None:
            return False
        return (
            option.weapon_caliber_inches is None
            or option.weapon_caliber_inches <= max_caliber
        )

    if option.option_kind == "special_weapon":
        return (
            mount.slot_type.code in {"weapon_front", "weapon_rear", "weapon_special"}
            and mount.special_weapon_capacity > 0
        )

    if option.option_kind in {"mortar", "mortar_launcher"}:
        return False

    # Normal positional weapons such as bow/stern assemblies are governed by
    # their normalized slot-type links only. Light/Medium/Heavy ceilings apply
    # only when the weapon itself references a class (currently broadsides).
    if option.weapon_class is None:
        return True
    if mount.max_weapon_class is None:
        return False
    return option.weapon_class.rank <= mount.max_weapon_class.rank
