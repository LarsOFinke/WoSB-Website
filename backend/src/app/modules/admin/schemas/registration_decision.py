from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.fleet.schemas.fleet_read import FleetRead

class RegistrationDecision(BaseModel):
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "RegistrationDecision":
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self
