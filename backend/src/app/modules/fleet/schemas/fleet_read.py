from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.fleet.schemas.fleet_membership_read import FleetMembershipRead

class FleetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    focus: str
    description: str | None = None
    standing_orders: str | None = None
    sort_order: int
    is_active: bool
    active_members_count: int = 0
    pending_members_count: int = 0
    leaders: list[FleetMembershipRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
