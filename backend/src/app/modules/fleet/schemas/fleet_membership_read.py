from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.fleet.schemas.fleet_member_user_read import FleetMemberUserRead

class FleetMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fleet_id: int
    user_id: int
    role: str
    status: str
    note: str | None = None
    assignment: str | None = None
    availability: str | None = None
    preferred_ships: str | None = None
    preferred_roles: str | None = None
    timezone: str | None = None
    discord_handle: str | None = None
    admin_note: str | None = None
    joined_at: datetime
    updated_at: datetime
    user: FleetMemberUserRead
