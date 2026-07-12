from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildItemOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_key: str
    name: str
    source: str | None = None
    notes: str | None = None
    image_url: str | None = None
    option_kind: str | None = None
    allowed_slot_types: list[str] = Field(default_factory=list)
    weapon_class: str | None = None
    weapon_caliber_inches: float | None = None
    stat_effects: dict[str, int | float] = Field(default_factory=dict)
    base_stat_effects: dict[str, int | float] = Field(default_factory=dict)
    is_ship_specific: bool = False
    sort_order: int
    created_at: datetime
    updated_at: datetime
