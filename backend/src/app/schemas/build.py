from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.ship import ShipRead

BUILD_TYPE_VALUES = {"balanced", "gunnery", "boarding", "defensive"}
WEAPON_ARC_KEYS = ("front", "rear", "port", "starboard")
WEAPON_SLOT_FIELDS = tuple(f"{arc}_weapon_slots" for arc in WEAPON_ARC_KEYS)


class InventorySlot(BaseModel):
    item: str = Field(min_length=1, max_length=160)
    quantity: int = Field(default=1, ge=1, le=999_999)

    @model_validator(mode="after")
    def normalize_item(self) -> "InventorySlot":
        self.item = self.item.strip()
        return self


class BuildStatRow(BaseModel):
    key: str
    label: str
    category: str
    base: int | float | None = None
    modifier: int | float | None = None
    effective: int | float | None = None
    unit: str | None = None
    precision: int = 0
    modifier_kind: str = "flat"
    effect_key: str | None = None
    is_debuff: bool = False
    source: str | None = None


class ShipStats(BaseModel):
    crew_total: int
    crew_capacity: int
    crew_remaining: int
    sailor_minimum: int
    sailors_required_met: bool
    upgrade_slots_used: int
    upgrade_slots_available: int
    base_upgrade_slots_available: int | None = None
    extra_upgrade_slots: int = 0
    ship_extra_upgrade_slots: int = 0
    upgrade_slot_5_unlocked: bool = False
    upgrade_slot_6_available: bool = False
    upgrade_slot_6_unlocked: bool = False
    base_crew_capacity: int | None = None
    effective_crew_capacity: int | None = None
    base_sailor_minimum: int | None = None
    effective_sailor_minimum: int | None = None
    upgrade_effects: dict[str, int | float] = Field(default_factory=dict)
    upgrade_buffs: dict[str, int | float] = Field(default_factory=dict)
    upgrade_debuffs: dict[str, int | float] = Field(default_factory=dict)
    base_stats: dict[str, int | float | str | None] = Field(default_factory=dict)
    effective_stats: dict[str, int | float | None] = Field(default_factory=dict)
    stat_rows: list[BuildStatRow] = Field(default_factory=list)
    stat_warnings: list[str] = Field(default_factory=list)
    weapon_slots: dict[str, int]
    weapon_total: int
    special_crew_total: int
    inventory_slots_used: int
    ammunition_slots_used: int
    consumable_slots_used: int
    hold_slots_used: int


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


class BuildCreate(BuildBase):
    pass


class BuildRead(BuildBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None = None
    ship: ShipRead
    ship_stats: ShipStats
    created_at: datetime
    updated_at: datetime
