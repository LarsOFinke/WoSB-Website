from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    fleet_id: int | None = None
    wants_fleet_membership: bool = False
    fleet_application_note: str | None = Field(default=None, max_length=1000)
    fleet_availability: str | None = Field(default=None, max_length=240)
    fleet_preferred_ships: str | None = Field(default=None, max_length=300)
    fleet_timezone: str | None = Field(default=None, max_length=80)
    fleet_discord_handle: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "RegisterRequest":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        if isinstance(self.fleet_name, str):
            self.fleet_name = self.fleet_name.strip() or None
        for field_name in ["fleet_application_note", "fleet_availability", "fleet_preferred_ships", "fleet_timezone", "fleet_discord_handle"]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.strip() or None)
        if self.fleet_id is not None:
            self.wants_fleet_membership = True
        return self
