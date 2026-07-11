from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
    availability: str | None = None
    timezone: str | None = None
    discord_handle: str | None = None
    preferred_ship_ids: list[int] = []
    preferred_role_ids: list[int] = []
    note: str | None = None
    created_at: datetime
