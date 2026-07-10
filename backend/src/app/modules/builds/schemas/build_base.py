from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.ships.schemas.ship import ShipRead

from app.modules.builds.schemas.constants import BUILD_TYPE_VALUES
from app.modules.builds.schemas.inventory_slot import InventorySlot

class BuildBase(BaseModel):
    build_name: str = Field(min_length=1, max_length=140)
    build_type: str = Field(default="balanced", max_length=32)
    ship_id: int

    sails: str | None = Field(default=None, max_length=140)
    upgrade_1: str | None = Field(default=None, max_length=140)
    upgrade_2: str | None = Field(default=None, max_length=140)
    upgrade_3: str | None = Field(default=None, max_length=140)
    upgrade_4: str | None = Field(default=None, max_length=140)
    upgrade_5: str | None = Field(default=None, max_length=140)
    upgrade_6: str | None = Field(default=None, max_length=140)
    lantern: str | None = Field(default=None, max_length=140)

    sailors: int = Field(default=0, ge=0)
    soldiers: int = Field(default=0, ge=0)
    musketeers: int = Field(default=0, ge=0)
    mercenaries: int = Field(default=0, ge=0)

    front_weapon_slots: list[InventorySlot] = Field(default_factory=list, max_length=12)
    rear_weapon_slots: list[InventorySlot] = Field(default_factory=list, max_length=12)
    port_weapon_slots: list[InventorySlot] = Field(default_factory=list, max_length=12)
    starboard_weapon_slots: list[InventorySlot] = Field(default_factory=list, max_length=12)
    mortar_weapon_slots: list[InventorySlot] = Field(default_factory=list, max_length=8)
    special_crew_slots: list[InventorySlot] = Field(default_factory=list, max_length=8)
    ammunition_slots: list[InventorySlot] = Field(default_factory=list, max_length=16)
    consumable_slots: list[InventorySlot] = Field(default_factory=list, max_length=3)
    hold_slots: list[InventorySlot] = Field(default_factory=list, max_length=32)
    details: str | None = Field(default=None, max_length=3000)

    @field_validator("build_type")
    @classmethod
    def validate_build_type(cls, value: str) -> str:
        normalized = value.strip().lower() if isinstance(value, str) else "balanced"
        if normalized not in BUILD_TYPE_VALUES:
            raise ValueError("Invalid build type.")
        return normalized

    @field_validator(
        "front_weapon_slots",
        "rear_weapon_slots",
        "port_weapon_slots",
        "starboard_weapon_slots",
        "mortar_weapon_slots",
        "special_crew_slots",
        "ammunition_slots",
        "consumable_slots",
        "hold_slots",
        mode="before",
    )
    @classmethod
    def normalize_slot_lists(cls, value: object) -> list[dict[str, object]]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            stripped = value.strip()
            return [{"item": stripped, "quantity": 1}] if stripped else []
        if not isinstance(value, list):
            raise ValueError("Slots must be submitted as a list.")

        cleaned: list[dict[str, object]] = []
        for slot in value:
            item: str | None = None
            quantity = 1

            if isinstance(slot, str):
                item = slot.strip()
            elif isinstance(slot, dict):
                raw_item = slot.get("item")
                if raw_item is None:
                    continue
                item = str(raw_item).strip()
                raw_quantity = slot.get("quantity", 1)
                try:
                    quantity = int(raw_quantity)
                except (TypeError, ValueError):
                    quantity = 1
            else:
                raise ValueError("Slot values must be strings or objects.")

            if item:
                cleaned.append({"item": item[:160], "quantity": max(quantity, 1)})
        return cleaned

    @model_validator(mode="after")
    def normalize_strings(self) -> "BuildBase":
        for field_name in (
            "sails",
            "upgrade_1",
            "upgrade_2",
            "upgrade_3",
            "upgrade_4",
            "upgrade_5",
            "upgrade_6",
            "lantern",
            "details",
        ):
            value = getattr(self, field_name)
            if isinstance(value, str):
                stripped = value.strip()
                setattr(self, field_name, stripped or None)
        self.build_name = self.build_name.strip()
        return self
