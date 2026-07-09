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
    stat_effects: dict[str, int | float] = Field(default_factory=dict)
    sort_order: int
    created_at: datetime
    updated_at: datetime


class BuildOptionsCatalog(BaseModel):
    categories: list[BuildItemCategoryRead]
    options: dict[str, list[BuildItemOptionRead]]
