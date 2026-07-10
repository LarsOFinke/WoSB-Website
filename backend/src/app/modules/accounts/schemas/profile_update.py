from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.constants import PREFERRED_FOCUS_VALUES

class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    fleet_id: int | None = None
    preferred_focus: str | None = Field(default=None, max_length=80)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "ProfileUpdate":
        self.display_name = self.display_name.strip()
        if isinstance(self.fleet_name, str):
            self.fleet_name = self.fleet_name.strip() or None
        if isinstance(self.preferred_focus, str):
            self.preferred_focus = self.preferred_focus.strip() or None
            if self.preferred_focus and self.preferred_focus not in PREFERRED_FOCUS_VALUES:
                raise ValueError("Invalid preferred focus.")
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self
