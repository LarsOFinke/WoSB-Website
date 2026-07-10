from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.modules.calendar.schemas.constants import FLEET_EVENT_CATEGORY_VALUES


class FleetEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(default="other", max_length=80)
    description: str | None = Field(default=None, max_length=3000)
    location: str | None = Field(default=None, max_length=200)
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    squad_id: int | None = None

    @model_validator(mode="after")
    def normalize(self) -> "FleetEventCreate":
        self.title = self.title.strip()
        self.category = self.category.strip().lower() or "other"
        if self.category not in FLEET_EVENT_CATEGORY_VALUES:
            raise ValueError("Invalid event category.")
        if isinstance(self.description, str):
            self.description = self.description.strip() or None
        if isinstance(self.location, str):
            self.location = self.location.strip() or None
        if self.end_at <= self.start_at:
            raise ValueError("Event end must be after event start.")
        return self
