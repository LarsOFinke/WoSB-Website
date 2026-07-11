from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class FleetJoinRequest(BaseModel):
    fleet_id: int | None = None
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "FleetJoinRequest":
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self
