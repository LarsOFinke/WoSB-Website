from __future__ import annotations

from dataclasses import dataclass

BASE_UPGRADE_SLOT_LIMIT = 4
UPGRADE_SLOT_LIMIT = 7
STANDARD_SHIP_UPGRADE_SLOTS = 5


@dataclass(frozen=True)
class UpgradeSlotAccess:
    base_slots: int
    slot_5_unlocked: bool
    slot_6_available: bool
    slot_7_available: bool
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
    """Calculate the seven-slot Build Designer access model.

    Slots 1-4 are always the regular ship slots. Three independent sources can
    extend that rack by one usable slot each:

    * the ship-line research reward,
    * the net slot unlocked by an expansion upgrade such as Structural
      Expansion, and
    * a ship-specific extra slot (for example La Couronne).

    ``ship_upgrade_slots`` keeps the existing seed/admin contract: five denotes
    a normal ship and six denotes one built-in ship extra. Values above six are
    accepted for future exceptional ships. ``unlock_effect_slots`` is already
    the *net* number of usable slots produced by installed expansion upgrades;
    the upgrade that creates those slots occupies one slot itself.
    """

    configured_slots = max(int(ship_upgrade_slots or 0), 0)
    base_slots = min(configured_slots, BASE_UPGRADE_SLOT_LIMIT)
    research_slots = 1 if research_upgrade_slot_unlocked else 0
    ship_extra_slots = min(
        max(configured_slots - STANDARD_SHIP_UPGRADE_SLOTS, 0),
        UPGRADE_SLOT_LIMIT - base_slots,
    )
    effect_slots = min(
        max(int(unlock_effect_slots or 0), 0),
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
        unlock_effect_slots=effect_slots,
        research_slots=research_slots,
        ship_extra_slots=ship_extra_slots,
        available_slots=available_slots,
    )
