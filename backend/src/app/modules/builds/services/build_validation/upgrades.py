from __future__ import annotations

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access
from app.modules.ships.models.ship import Ship

from .options import BuildOptionCatalog


class UpgradeAccessEvaluator:
    @staticmethod
    def evaluate(
        ship: Ship,
        selected_upgrades: dict[int, BuildItemOption],
        *,
        research_upgrade_slot_unlocked: bool,
    ) -> dict[str, int | bool]:
        pre_expansion = calculate_upgrade_slot_access(
            ship_upgrade_slots=int(ship.upgrade_slots or 0),
            unlock_effect_slots=0,
            research_upgrade_slot_unlocked=research_upgrade_slot_unlocked,
        )
        unlock_effect_slots = sum(
            max(
                0,
                int(BuildOptionCatalog.effects(option, ship).get("extra_upgrade_slots", 0) or 0),
            )
            for index, option in selected_upgrades.items()
            if index <= pre_expansion.available_slots
        )
        access = calculate_upgrade_slot_access(
            ship_upgrade_slots=int(ship.upgrade_slots or 0),
            unlock_effect_slots=unlock_effect_slots,
            research_upgrade_slot_unlocked=research_upgrade_slot_unlocked,
        )
        return {
            "base_slots": access.base_slots,
            "slot_5_unlocked": access.slot_5_unlocked,
            "slot_6_available": access.slot_6_available,
            "slot_7_available": access.slot_7_available,
            "slot_8_available": access.slot_8_available,
            "unlock_effect_slots": access.unlock_effect_slots,
            "research_slots": access.research_slots,
            "ship_extra_slots": access.ship_extra_slots,
            "available_slots": access.available_slots,
        }
