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
        capacities = self._capacities(ship, build)
        for field_name, slot_type in WEAPON_SLOT_TYPE_BY_FIELD.items():
            slots = getattr(build, field_name)
            label = WEAPON_FIELD_LABELS[field_name]
            UniqueSlotValidator.validate(slots, label)
            self._validate_row_and_capacity(field_name, label, slots, capacities[field_name])
            selected_options: list[tuple[BuildItemOption, int]] = []
            for slot in slots:
                option = BuildOptionCatalog.require(option_map, slot.item, "weapon", label)
                self._validate_mount(ship, build, option, slot_type, label)
                selected_options.append((option, int(slot.quantity or 1)))
            self._validate_special_capacity(
                ship,
                slot_type,
                label,
                selected_options,
            )

    @staticmethod
    def _capacities(ship: Ship, build: BuildCreate) -> dict[str, int]:
        installed = build.mortar_modification_installed
        return {
            "front_weapon_slots": ship.effective_weapon_capacity(
                "weapon_front",
                mortar_modification_installed=installed,
            ),
            "rear_weapon_slots": ship.effective_weapon_capacity(
                "weapon_rear",
                mortar_modification_installed=installed,
            ),
            "port_weapon_slots": ship.effective_weapon_capacity(
                "weapon_port",
                mortar_modification_installed=installed,
            ),
            "starboard_weapon_slots": ship.effective_weapon_capacity(
                "weapon_starboard",
                mortar_modification_installed=installed,
            ),
            "mortar_weapon_slots": ship.effective_weapon_capacity(
                "weapon_mortar",
                mortar_modification_installed=installed,
            ),
            "special_weapon_slots": ship.effective_weapon_capacity(
                "weapon_special",
                mortar_modification_installed=installed,
            ),
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
        ship: Ship,
        build: BuildCreate,
        option: BuildItemOption,
        slot_type: str,
        label: str,
    ) -> None:
        if slot_type not in option.allowed_slots:
            raise BuildValidationError(
                f"{label}: '{option.name}' cannot be mounted in this slot type."
            )
        if slot_type == "weapon_mortar":
            WeaponLoadoutValidator._validate_mortar(ship, build, option, label)
        mount = ship._mount(slot_type)
        installed = build.mortar_modification_installed
        if mount is None or not is_weapon_compatible(
            option,
            mount,
            capacity_override=ship.effective_weapon_capacity(
                slot_type,
                mortar_modification_installed=installed,
            ),
            max_caliber_override=(
                ship.effective_max_mortar_caliber_inches(
                    mortar_modification_installed=installed
                )
                if slot_type == "weapon_mortar"
                else None
            ),
        ):
            raise BuildValidationError(
                f"{label}: '{option.name}' is not compatible with this ship's mount profile."
            )
        if slot_type == "weapon_mortar":
            return
        if slot_type == "weapon_special":
            if option.option_kind != "special_weapon":
                raise BuildValidationError(
                    f"{label}: '{option.name}' is not a special weapon."
                )
        elif option.option_kind == "special_weapon":
            if slot_type not in {"weapon_front", "weapon_rear"}:
                raise BuildValidationError(
                    f"{label}: '{option.name}' is not valid for this positional mount."
                )
        elif option.option_kind in {"mortar", "mortar_launcher"}:
            raise BuildValidationError(
                f"{label}: '{option.name}' must be placed in its dedicated slot."
            )

    @staticmethod
    def _validate_special_capacity(
        ship: Ship,
        slot_type: str,
        label: str,
        selected_options: list[tuple[BuildItemOption, int]],
    ) -> None:
        special_quantity = sum(
            quantity
            for option, quantity in selected_options
            if option.option_kind == "special_weapon"
        )
        special_capacity = ship.special_weapon_capacity_for(slot_type)
        if special_quantity > special_capacity:
            raise BuildValidationError(
                f"{label}: selected special-weapon quantity ({special_quantity}) exceeds "
                f"this mount's special capacity ({special_capacity})."
            )

    @staticmethod
    def _validate_mortar(
        ship: Ship,
        build: BuildCreate,
        option: BuildItemOption,
        label: str,
    ) -> None:
        max_caliber = ship.effective_max_mortar_caliber_inches(
            mortar_modification_installed=build.mortar_modification_installed
        )
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
