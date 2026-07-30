from __future__ import annotations

from dataclasses import dataclass

BASE_UPGRADE_SLOT_LIMIT = 4
UPGRADE_SLOT_LIMIT = 8
STANDARD_SHIP_UPGRADE_SLOTS = 5


@dataclass(frozen=True)
class UpgradeSlotAccess:
    base_slots: int
    slot_5_unlocked: bool
    slot_6_available: bool
    slot_7_available: bool
    slot_8_available: bool
    unlock_effect_slots: int
    research_slots: int
    ship_extra_slots: int
    available_slots: int


def calculate_upgrade_slot_access(
    *,
    ship_upgrade_slots: int,
    unlock_effect_slots: int = 0,
    research_upgrade_slots: int = 0,
) -> UpgradeSlotAccess:
    """Calculate the eight-slot Build Designer access model.

    Slots 1-4 are the regular rack. The remaining capacity comes from the
    actual in-game slot sources:

    * the configured build feature grants its normalized slot count,
    * expansion upgrades grant their full ``extra_upgrade_slots`` value, and
    * exceptional ships can provide built-in slots (for example La Couronne).

    Structural Expansion therefore contributes two rack positions. It still
    consumes one selected position like every other upgrade; that occupancy is
    represented by the build itself and must not be subtracted from capacity.

    ``ship_upgrade_slots`` keeps the existing seed/admin contract: five denotes
    a normal ship and six denotes one built-in ship extra. Zero denotes a ship
    without an upgrade rack; research and expansion effects cannot create one.
    Values above six are accepted for future exceptional ships.
    ``unlock_effect_slots`` is the gross number of positions granted by installed
    expansion upgrades.
    """

    configured_slots = max(int(ship_upgrade_slots or 0), 0)
    base_slots = min(configured_slots, BASE_UPGRADE_SLOT_LIMIT)
    has_upgrade_rack = configured_slots > 0
    research_slots = (
        min(max(int(research_upgrade_slots or 0), 0), UPGRADE_SLOT_LIMIT - base_slots)
        if has_upgrade_rack
        else 0
    )
    ship_extra_slots = min(
        max(configured_slots - STANDARD_SHIP_UPGRADE_SLOTS, 0),
        UPGRADE_SLOT_LIMIT - base_slots,
    )
    effect_slots = min(
        max(int(unlock_effect_slots or 0), 0) if has_upgrade_rack else 0,
        UPGRADE_SLOT_LIMIT - base_slots,
    )

    extra_slots = min(
        research_slots + ship_extra_slots + effect_slots,
        UPGRADE_SLOT_LIMIT - base_slots,
    )
    available_slots = min(UPGRADE_SLOT_LIMIT, base_slots + extra_slots)

    return UpgradeSlotAccess(
        base_slots=base_slots,
        slot_5_unlocked=available_slots >= 5,
        slot_6_available=available_slots >= 6,
        slot_7_available=available_slots >= 7,
        slot_8_available=available_slots >= 8,
        unlock_effect_slots=effect_slots,
        research_slots=research_slots,
        ship_extra_slots=ship_extra_slots,
        available_slots=available_slots,
    )
