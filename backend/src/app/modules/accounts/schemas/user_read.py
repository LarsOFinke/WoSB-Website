from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    fleet_name: str | None = None
    fleet_id: int | None = None
    fleet_membership_id: int | None = None
    fleet_membership_status: str | None = None
    fleet_membership_role: str | None = None
    preferred_focus: str | None = None
    note: str | None = None
    created_at: datetime
