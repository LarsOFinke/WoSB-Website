from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class SeedMetadataRead(BaseModel):
    seed_key: str | None = None
    seed_revision: str | None = None
    is_seed_overridden: bool = False
    seed_status: str


class MasterDataOverview(BaseModel):
    category_count: int
    option_count: int
    ship_count: int
    overridden_count: int
    inactive_count: int


class MasterDataCategoryBase(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(default=100, ge=0, le=100000)
    is_active: bool = True

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        return value.strip()


class MasterDataCategoryCreate(MasterDataCategoryBase):
    key: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_]*$")


class MasterDataCategoryUpdate(MasterDataCategoryBase):
    pass


class MasterDataCategoryRead(MasterDataCategoryBase, SeedMetadataRead):
    id: int
    key: str
    created_at: datetime
    updated_at: datetime


class MasterDataOptionBase(BaseModel):
    category_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=160)
    source: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    option_kind: str | None = Field(default=None, max_length=40)
    weapon_class: str | None = Field(default=None, max_length=24)
    weapon_caliber_inches: float | None = Field(default=None, ge=0)
    stat_effects: dict[str, float] = Field(default_factory=dict)
    allowed_slot_types: list[str] = Field(default_factory=list)
    sort_order: int = Field(default=100, ge=0, le=100000)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("source", "notes", "image_url", "option_kind", "weapon_class")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("stat_effects")
    @classmethod
    def validate_effects(cls, value: dict[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for key, number in value.items():
            clean_key = key.strip()
            if not clean_key or len(clean_key) > 80 or not clean_key.replace("_", "").isalnum():
                raise ValueError(f"Invalid stat effect key: {key}")
            normalized[clean_key] = float(number)
        return normalized

    @field_validator("allowed_slot_types")
    @classmethod
    def normalize_slot_types(cls, value: list[str]) -> list[str]:
        return sorted({item.strip() for item in value if item.strip()})


class MasterDataOptionCreate(MasterDataOptionBase):
    pass


class MasterDataOptionUpdate(MasterDataOptionBase):
    pass


class MasterDataOptionRead(MasterDataOptionBase, SeedMetadataRead):
    id: int
    category_key: str
    category_label: str
    created_at: datetime
    updated_at: datetime


class MasterDataShipMount(BaseModel):
    slot_type: str = Field(min_length=1, max_length=40)
    capacity: int = Field(default=0, ge=0, le=1000)
    max_weapon_class: str | None = Field(default=None, max_length=24)
    max_caliber_inches: float | None = Field(default=None, ge=0)

    @field_validator("slot_type")
    @classmethod
    def strip_slot_type(cls, value: str) -> str:
        return value.strip()

    @field_validator("max_weapon_class")
    @classmethod
    def normalize_weapon_class(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class MasterDataShipUpgradeOverride(BaseModel):
    option_id: int = Field(ge=1)
    stat_effects: dict[str, float] = Field(default_factory=dict)

    @field_validator("stat_effects")
    @classmethod
    def validate_override_effects(cls, value: dict[str, float]) -> dict[str, float]:
        return MasterDataOptionBase.validate_effects(value)


class MasterDataShipUpgradeOverrideRead(MasterDataShipUpgradeOverride):
    option_name: str
    base_stat_effects: dict[str, float] = Field(default_factory=dict)
    effective_stat_effects: dict[str, float] = Field(default_factory=dict)


class MasterDataShipBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rate: int = Field(ge=1, le=7)
    ship_type: str = Field(min_length=1, max_length=80)
    durability: int = Field(default=0, ge=0)
    speed_min_knots: float = Field(default=0, ge=0)
    speed_knots: float = Field(default=0, ge=0)
    maneuverability: float = Field(default=0, ge=0)
    armor: float = Field(default=0, ge=0)
    hold_capacity: int = Field(default=0, ge=0)
    crew_capacity: int = Field(default=100, ge=0)
    sailor_minimum: int = Field(default=0, ge=0)
    displacement_tons: int = Field(default=0, ge=0)
    source: str | None = Field(default=None, max_length=240)
    image_url: str | None = Field(default=None, max_length=500)
    sail_slots: int = Field(default=1, ge=0, le=20)
    upgrade_slots: int = Field(default=5, ge=0, le=8)
    has_lantern: bool = True
    is_active: bool = True
    weapon_mounts: list[MasterDataShipMount] = Field(default_factory=list)
    upgrade_effect_overrides: list[MasterDataShipUpgradeOverride] = Field(default_factory=list)

    @field_validator("name", "ship_type")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("source", "image_url")
    @classmethod
    def normalize_ship_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_ship(self) -> "MasterDataShipBase":
        if self.sailor_minimum > self.crew_capacity:
            raise ValueError("Sailor minimum cannot exceed crew capacity.")
        if self.speed_knots < self.speed_min_knots:
            raise ValueError("Cruise maximum speed cannot be lower than base speed.")
        option_ids = [row.option_id for row in self.upgrade_effect_overrides]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("Each upgrade can only be overridden once per ship.")
        slot_types = [row.slot_type for row in self.weapon_mounts]
        if len(slot_types) != len(set(slot_types)):
            raise ValueError("Each weapon slot type can only occur once per ship.")
        return self


class MasterDataShipCreate(MasterDataShipBase):
    pass


class MasterDataShipUpdate(MasterDataShipBase):
    pass


class MasterDataShipRead(MasterDataShipBase, SeedMetadataRead):
    id: int
    upgrade_effect_overrides: list[MasterDataShipUpgradeOverrideRead] = Field(default_factory=list)
    weapon_layout: str
    created_at: datetime
    updated_at: datetime


class WeaponClassRead(BaseModel):
    code: str
    label: str
    rank: int


class WeaponSlotTypeRead(BaseModel):
    code: str
    label: str
    sort_order: int


class MasterDataTaxonomyRead(BaseModel):
    weapon_classes: list[WeaponClassRead]
    weapon_slot_types: list[WeaponSlotTypeRead]
