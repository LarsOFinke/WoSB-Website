from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildItemCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    label: str
    sort_order: int


class BuildItemOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_key: str
    name: str
    source: str | None = None
    notes: str | None = None
    option_kind: str | None = None
    allowed_slot_types: list[str] = Field(default_factory=list)
    weapon_caliber_inches: float | None = None
    stat_effects: dict[str, int | float] = Field(default_factory=dict)
    sort_order: int
    created_at: datetime
    updated_at: datetime


class BuildStatDefinitionRead(BaseModel):
    key: str
    label: str
    category: str
    base_field: str | None = None
    unit: str | None = None
    pct_effect: str | None = None
    flat_effect: str | None = None
    precision: int = 0
    positive_is_good: bool = True
    source: str | None = None


class BuildOptionsCatalog(BaseModel):
    categories: list[BuildItemCategoryRead]
    options: dict[str, list[BuildItemOptionRead]]
    stat_definitions: list[BuildStatDefinitionRead] = Field(default_factory=list)
