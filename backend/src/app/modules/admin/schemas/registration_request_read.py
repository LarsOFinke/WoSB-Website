from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.fleet.schemas.fleet_read import FleetRead

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
