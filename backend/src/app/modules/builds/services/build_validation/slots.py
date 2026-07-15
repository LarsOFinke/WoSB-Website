from __future__ import annotations

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.builds.schemas.build_create import BuildCreate

from .constants import INVENTORY_SLOT_MAP, WEAPON_FIELD_LABELS, WEAPON_SLOT_TYPE_BY_FIELD
from .options import BuildOptionCatalog


class BuildSlotFactory:
    def create(
        self,
        build: BuildCreate,
        option_map: dict[tuple[str, str], BuildItemOption],
    ) -> list[BuildSlot]:
        slots: list[BuildSlot] = []
        self._append_single_slots(slots, build, option_map)
        self._append_upgrades(slots, build, option_map)
        self._append_weapons(slots, build, option_map)
        self._append_special_crew(slots, build, option_map)
        self._append_inventory(slots, build, option_map)
        return slots

    @staticmethod
    def _append_single_slots(slots: list[BuildSlot], build: BuildCreate, option_map: dict) -> None:
        if build.sails:
            option = BuildOptionCatalog.require(option_map, build.sails, "sail", "Sail")
            slots.append(BuildSlot(slot_type="sail", slot_index=1, option_id=option.id))
        if build.lantern:
            option = BuildOptionCatalog.require(option_map, build.lantern, "lantern", "Lantern")
            slots.append(BuildSlot(slot_type="lantern", slot_index=1, option_id=option.id))

    @staticmethod
    def _append_upgrades(slots: list[BuildSlot], build: BuildCreate, option_map: dict) -> None:
        for index, option in BuildOptionCatalog.selected_upgrades(option_map, build).items():
            slots.append(BuildSlot(slot_type="upgrade", slot_index=index, option_id=option.id))

    @staticmethod
    def _append_weapons(slots: list[BuildSlot], build: BuildCreate, option_map: dict) -> None:
        for field_name, slot_type in WEAPON_SLOT_TYPE_BY_FIELD.items():
            for index, slot in enumerate(getattr(build, field_name), start=1):
                option = BuildOptionCatalog.require(
                    option_map, slot.item, "weapon", WEAPON_FIELD_LABELS[field_name]
                )
                slots.append(
                    BuildSlot(
                        slot_type=slot_type,
                        slot_index=index,
                        option_id=option.id,
                        quantity=slot.quantity,
                    )
                )

    @staticmethod
    def _append_special_crew(slots: list[BuildSlot], build: BuildCreate, option_map: dict) -> None:
        for index, slot in enumerate(build.special_crew_slots, start=1):
            option = BuildOptionCatalog.require(
                option_map, slot.item, "special_crew", "Special crew"
            )
            slots.append(
                BuildSlot(
                    slot_type="special_crew",
                    slot_index=index,
                    option_id=option.id,
                    quantity=1,
                )
            )

    @staticmethod
    def _append_inventory(slots: list[BuildSlot], build: BuildCreate, option_map: dict) -> None:
        for slot_type, category_key in INVENTORY_SLOT_MAP.items():
            for index, slot in enumerate(getattr(build, f"{slot_type}_slots"), start=1):
                option = BuildOptionCatalog.require(
                    option_map, slot.item, category_key, slot_type.title()
                )
                slots.append(
                    BuildSlot(
                        slot_type=slot_type,
                        slot_index=index,
                        option_id=option.id,
                        quantity=slot.quantity,
                    )
                )
