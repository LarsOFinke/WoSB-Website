from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.fleet.schemas.constants import FLEET_ROLE_VALUES, FLEET_STATUS_VALUES

class FleetMembershipUpdate(BaseModel):
    role: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, max_length=40)
    note: str | None = Field(default=None, max_length=1000)
    assignment: str | None = Field(default=None, max_length=120)
    admin_note: str | None = Field(default=None, max_length=1200)

    @model_validator(mode="after")
    def normalize(self) -> "FleetMembershipUpdate":
        if isinstance(self.role, str):
            self.role = self.role.strip()
            if self.role not in FLEET_ROLE_VALUES:
                raise ValueError("Invalid fleet role.")
        if isinstance(self.status, str):
            self.status = self.status.strip()
            if self.status not in FLEET_STATUS_VALUES:
                raise ValueError("Invalid membership status.")
        for field_name in ["note", "assignment", "admin_note"]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.strip() or None)
        return self
