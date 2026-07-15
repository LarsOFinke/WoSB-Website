from __future__ import annotations

from app.core.password_policy import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RegisterRequest(BaseModel):
    """Account access request with an optional official-fleet application."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    display_name: str = Field(min_length=1, max_length=120)
    wants_fleet_membership: bool = False
    fleet_id: int | None = Field(default=None, gt=0)
    fleet_application_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "RegisterRequest":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        if isinstance(self.fleet_application_note, str):
            self.fleet_application_note = self.fleet_application_note.strip() or None
        if not self.wants_fleet_membership:
            if self.fleet_id is not None or self.fleet_application_note is not None:
                raise ValueError("Fleet application details require wants_fleet_membership=true.")
        return self
