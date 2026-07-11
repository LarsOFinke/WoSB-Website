from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.modules.accounts.schemas.constants import PREFERRED_FOCUS_VALUES


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    preferred_focus: str | None = Field(default=None, max_length=80)
    availability: str | None = Field(default=None, max_length=240)
    timezone: str | None = Field(default=None, max_length=80)
    discord_handle: str | None = Field(default=None, max_length=120)
    preferred_ship_ids: list[int] = Field(default_factory=list, max_length=20)
    preferred_role_ids: list[int] = Field(default_factory=list, max_length=10)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "ProfileUpdate":
        self.display_name = self.display_name.strip()
        for field_name in ["fleet_name", "preferred_focus", "availability", "timezone", "discord_handle", "note"]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.strip() or None)
        if self.preferred_focus and self.preferred_focus not in PREFERRED_FOCUS_VALUES:
            raise ValueError("Invalid preferred focus.")
        self.preferred_ship_ids = list(dict.fromkeys(self.preferred_ship_ids))
        self.preferred_role_ids = list(dict.fromkeys(self.preferred_role_ids))
        return self
