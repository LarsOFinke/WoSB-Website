from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.ship import ShipRead

BUILD_TYPE_VALUES = {"balanced", "gunnery", "boarding", "defensive"}


class InventorySlot(BaseModel):
    item: str = Field(min_length=1, max_length=160)
    quantity: int = Field(default=1, ge=1, le=999_999)

    @model_validator(mode="after")
    def normalize_item(self) -> "InventorySlot":
        self.item = self.item.strip()
        return self


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
    lantern: str | None = Field(default=None, max_length=140)

    sailors: int = Field(default=0, ge=0)
    soldiers: int = Field(default=0, ge=0)
    musketeers: int = Field(default=0, ge=0)
    mercenaries: int = Field(default=0, ge=0)

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

    @field_validator("ammunition_slots", "consumable_slots", "hold_slots", mode="before")
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
            "lantern",
            "details",
        ):
            value = getattr(self, field_name)
            if isinstance(value, str):
                stripped = value.strip()
                setattr(self, field_name, stripped or None)
        self.build_name = self.build_name.strip()
        return self


class BuildCreate(BuildBase):
    pass


class BuildRead(BuildBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None = None
    ship: ShipRead
    created_at: datetime
    updated_at: datetime
