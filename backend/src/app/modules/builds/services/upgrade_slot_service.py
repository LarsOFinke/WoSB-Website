from __future__ import annotations

from dataclasses import dataclass

BASE_UPGRADE_SLOT_LIMIT = 4
UPGRADE_SLOT_LIMIT = 6
SHIP_EXTRA_UPGRADE_SLOT = 6


@dataclass(frozen=True)
class UpgradeSlotAccess:
    base_slots: int
    slot_5_unlocked: bool
    slot_6_available: bool
    unlock_effect_slots: int
    research_slots: int
    ship_extra_slots: int
    available_slots: int


def calculate_upgrade_slot_access(
    *,
    ship_upgrade_slots: int,
    unlock_effect_slots: int = 0,
    research_upgrade_slot_unlocked: bool = False,
) -> UpgradeSlotAccess:
    """Calculate the six-slot Build Designer access model.

    Slots 1-4 are the regular slots. Slot 5 can be unlocked either by the
    account-wide ship-line research reward or by an equipment expansion effect.
    Slot 6 is available on explicitly six-slot ships or when two independent
    expansion slots are unlocked (for example research reward + one expansion
    upgrade). The returned count reflects individually usable slots, so a ship
    extra slot and the research reward stack correctly.
    """

    base_slots = min(max(int(ship_upgrade_slots or 0), 0), BASE_UPGRADE_SLOT_LIMIT)
    effect_slots = min(max(int(unlock_effect_slots or 0), 0), UPGRADE_SLOT_LIMIT - base_slots)
    research_slots = 1 if research_upgrade_slot_unlocked else 0
    non_ship_unlocks = min(effect_slots + research_slots, UPGRADE_SLOT_LIMIT - base_slots)
    ship_extra_slots = 1 if int(ship_upgrade_slots or 0) >= SHIP_EXTRA_UPGRADE_SLOT else 0

    slot_5_unlocked = non_ship_unlocks >= 1
    slot_6_available = ship_extra_slots > 0 or non_ship_unlocks >= 2
    available_slots = min(
        UPGRADE_SLOT_LIMIT,
        base_slots + int(slot_5_unlocked) + int(slot_6_available),
    )

    return UpgradeSlotAccess(
        base_slots=base_slots,
        slot_5_unlocked=slot_5_unlocked,
        slot_6_available=slot_6_available,
        unlock_effect_slots=effect_slots,
        research_slots=research_slots,
        ship_extra_slots=ship_extra_slots,
        available_slots=available_slots,
    )
