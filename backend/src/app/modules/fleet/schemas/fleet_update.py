from __future__ import annotations


from pydantic import BaseModel, Field, model_validator

from app.modules.fleet.schemas.constants import FLEET_FOCUS_VALUES

class FleetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    focus: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    standing_orders: str | None = Field(default=None, max_length=3000)
    sort_order: int | None = Field(default=None, ge=0, le=9999)
    is_active: bool | None = None

    @model_validator(mode="after")
    def normalize(self) -> "FleetUpdate":
        if isinstance(self.name, str):
            self.name = self.name.strip()
        if isinstance(self.slug, str):
            self.slug = self.slug.strip().lower().replace(" ", "-")
        if isinstance(self.focus, str):
            self.focus = self.focus.strip()
            if self.focus not in FLEET_FOCUS_VALUES:
                raise ValueError("Invalid fleet focus.")
        if isinstance(self.description, str):
            self.description = self.description.strip() or None
        if isinstance(self.standing_orders, str):
            self.standing_orders = self.standing_orders.strip() or None
        return self
