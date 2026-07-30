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

    Slot taxonomy is authoritative first. Standard broadside and bow/stern
    weapons both respect the mount's Light/Medium/Heavy ceiling. Mortars use
    their dedicated caliber limit, while audited special weapons use the
    separate special-capacity rule.
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

    if option.option_kind not in {"cannon", "bow_stern"}:
        return False
    if option.weapon_class is None or mount.max_weapon_class is None:
        # Fail closed for malformed or incomplete master data. Standard weapon
        # families must always carry a normalized size classification.
        return False
    return option.weapon_class.rank <= mount.max_weapon_class.rank
