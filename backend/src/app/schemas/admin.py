from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.auth import UserRead
from app.schemas.fleet import FleetRead


class ModeratorCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "ModeratorCreate":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        return self


class ModeratorCreateResponse(BaseModel):
    user: UserRead


class RegistrationDecision(BaseModel):
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "RegistrationDecision":
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self


class RegistrationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    external_fleet_name: str | None = None
    fleet_id: int | None = None
    wants_fleet_membership: bool = False
    fleet_application_note: str | None = None
    fleet_availability: str | None = None
    fleet_preferred_ships: str | None = None
    fleet_timezone: str | None = None
    fleet_discord_handle: str | None = None
    status: str
    decision_note: str | None = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: datetime | None = None
    fleet: FleetRead | None = None
    reviewed_by: UserRead | None = None
    created_user: UserRead | None = None


class AppLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    level: str
    logger: str
    message: str
    request_id: str | None = None
    method: str | None = None
    path: str | None = None
    status_code: int | None = None
    duration_ms: float | None = None
    client: str | None = None
    exception: str | None = None


class AppLogSummary(BaseModel):
    total: int
    errors: int
    warnings: int
    slow_requests: int
    recent_status: dict[str, int]
