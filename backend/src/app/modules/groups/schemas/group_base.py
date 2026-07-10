from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.groups.models.group import GROUP_FOCUS_VALUES
from app.modules.ships.schemas.ship import ShipRead
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.builds.schemas.build_read import BuildRead

class GroupBase(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    focus: str = Field(default="pve_general", max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    expectations: str | None = Field(default=None, max_length=2000)
    activity_plan: str | None = Field(default=None, max_length=2000)
    contact_note: str | None = Field(default=None, max_length=300)
    scheduled_start_at: datetime | None = None
    scheduled_end_at: datetime | None = None
    max_members: int = Field(default=5, ge=2, le=50)
    min_ship_rate: int | None = Field(default=None, ge=1, le=7)
    max_ship_rate: int | None = Field(default=None, ge=1, le=7)
    allow_guests: bool = True
    fleet_restriction: str | None = Field(default=None, max_length=120)

    @field_validator("focus")
    @classmethod
    def validate_focus(cls, value: str) -> str:
        normalized = value.strip().lower() if isinstance(value, str) else "pve_general"
        if normalized not in GROUP_FOCUS_VALUES:
            raise ValueError("Invalid group focus.")
        return normalized

    @model_validator(mode="after")
    def normalize_strings(self) -> "GroupBase":
        if self.min_ship_rate is not None and self.max_ship_rate is not None and self.max_ship_rate > self.min_ship_rate:
            raise ValueError("Maximum rate must be numerically lower than or equal to minimum rate.")
        if self.scheduled_start_at and self.scheduled_end_at and self.scheduled_end_at <= self.scheduled_start_at:
            raise ValueError("End time must be after start time.")
        for field_name in ("title", "description", "expectations", "activity_plan", "contact_note", "fleet_restriction"):
            value = getattr(self, field_name)
            if isinstance(value, str):
                stripped = value.strip()
                setattr(self, field_name, stripped or None)
        return self
