from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

class RegistrationRequestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    wants_fleet_membership: bool = False
    fleet_id: int | None = None
    fleet_application_note: str | None = None
    status: str
    created_at: datetime
