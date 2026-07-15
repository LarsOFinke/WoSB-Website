from __future__ import annotations

from pydantic import BaseModel, Field


class FleetPublicLeaderRead(BaseModel):
    display_name: str
    role: str
    role_label: str


class FleetPublicRead(BaseModel):
    id: int
    name: str
    slug: str
    focus: str
    description: str | None = None
    standing_orders: str | None = None
    active_members_count: int = 0
    leaders: list[FleetPublicLeaderRead] = Field(default_factory=list)
