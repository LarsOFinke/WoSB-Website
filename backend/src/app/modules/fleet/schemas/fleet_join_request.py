from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

class FleetJoinRequest(BaseModel):
    fleet_id: int | None = None
    note: str | None = Field(default=None, max_length=1000)
    availability: str | None = Field(default=None, max_length=240)
    preferred_ships: str | None = Field(default=None, max_length=300)
    timezone: str | None = Field(default=None, max_length=80)
    discord_handle: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "FleetJoinRequest":
        for field_name in ["note", "availability", "preferred_ships", "timezone", "discord_handle"]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.strip() or None)
        return self
