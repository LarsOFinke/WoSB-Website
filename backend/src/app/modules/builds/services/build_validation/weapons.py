from __future__ import annotations

from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.inventory_slot import InventorySlot
from app.modules.builds.services.build_limits import (
    DEDICATED_WEAPON_ROW_LIMIT,
    WEAPON_ARC_ROW_LIMIT,
)
from app.modules.ships.models.ship import Ship
from app.modules.ships.services.weapon_compatibility import is_weapon_compatible

from .constants import WEAPON_FIELD_LABELS, WEAPON_SLOT_TYPE_BY_FIELD
from .errors import BuildValidationError
from .options import BuildOptionCatalog


class UniqueSlotValidator:
    @staticmethod
    def validate(slots: list[InventorySlot], label: str) -> None:
        normalized = [slot.item.casefold() for slot in slots]
        if len(normalized) != len(set(normalized)):
            raise BuildValidationError(
                f"{label}: an item can only be selected once. "
                "Same items stack in one inventory slot."
            )


class WeaponLoadoutValidator:
    def validate(
        self,
        ship: Ship,
        build: BuildCreate,
        option_map: dict[tuple[str, str], BuildItemOption],
    ) -> None:
        capacities = self._capacities(ship)
        for field_name, slot_type in WEAPON_SLOT_TYPE_BY_FIELD.items():
            slots = getattr(build, field_name)
            label = WEAPON_FIELD_LABELS[field_name]
            UniqueSlotValidator.validate(slots, label)
            self._validate_row_and_capacity(field_name, label, slots, capacities[field_name])
            for slot in slots:
                option = BuildOptionCatalog.require(option_map, slot.item, "weapon", label)
                self._validate_mount(ship, option, slot_type, label)

    @staticmethod
    def _capacities(ship: Ship) -> dict[str, int]:
        return {
            "front_weapon_slots": int(ship.front_weapon_capacity or 0),
            "rear_weapon_slots": int(ship.rear_weapon_capacity or 0),
            "port_weapon_slots": int(ship.broadside_weapon_capacity or 0),
            "starboard_weapon_slots": int(ship.broadside_weapon_capacity or 0),
            "mortar_weapon_slots": int(ship.mortar_weapon_capacity or 0),
            "special_weapon_slots": int(ship.special_weapon_capacity or 0),
        }

    @staticmethod
    def _validate_row_and_capacity(
        field_name: str, label: str, slots: list[InventorySlot], capacity: int
    ) -> None:
        row_limit = (
            DEDICATED_WEAPON_ROW_LIMIT
            if field_name in {"mortar_weapon_slots", "special_weapon_slots"}
            else WEAPON_ARC_ROW_LIMIT
        )
        if len(slots) > row_limit:
            raise BuildValidationError(f"{label} are limited to {row_limit} item rows.")
        quantity_total = sum(slot.quantity or 1 for slot in slots)
        if quantity_total > capacity:
            raise BuildValidationError(
                f"{label}: selected quantity ({quantity_total}) exceeds "
                f"this ship's capacity ({capacity})."
            )
        if quantity_total > 0 and capacity <= 0:
            raise BuildValidationError(
                f"{label}: this ship has no valid slots for that weapon position."
            )

    @staticmethod
    def _validate_mount(
        ship: Ship, option: BuildItemOption, slot_type: str, label: str
    ) -> None:
        if slot_type not in option.allowed_slots:
            raise BuildValidationError(
                f"{label}: '{option.name}' cannot be mounted in this slot type."
            )
        mount = ship._mount(slot_type)
        if mount is None or not is_weapon_compatible(option, mount):
            raise BuildValidationError(
                f"{label}: '{option.name}' is not compatible with this ship's mount profile."
            )
        if slot_type == "weapon_mortar":
            WeaponLoadoutValidator._validate_mortar(ship, option, label)
        elif slot_type == "weapon_special":
            if option.option_kind != "special_weapon":
                raise BuildValidationError(
                    f"{label}: '{option.name}' is not a special weapon."
                )
        elif option.option_kind in {"mortar", "mortar_launcher", "special_weapon"}:
            raise BuildValidationError(
                f"{label}: '{option.name}' must be placed in its dedicated slot."
            )

    @staticmethod
    def _validate_mortar(ship: Ship, option: BuildItemOption, label: str) -> None:
        max_caliber = ship.max_mortar_caliber_inches
        if option.option_kind not in {"mortar", "mortar_launcher"}:
            raise BuildValidationError(
                f"{label}: '{option.name}' is not a mortar-slot weapon."
            )
        if (
            max_caliber is not None
            and option.weapon_caliber_inches is not None
            and option.weapon_caliber_inches > float(max_caliber)
        ):
            raise BuildValidationError(
                f"{label}: '{option.name}' exceeds this ship's mortar caliber "
                f"limit ({max_caliber} in)."
            )
