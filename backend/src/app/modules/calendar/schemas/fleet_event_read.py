from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.accounts.schemas.user_reference_read import UserReferenceRead
from app.modules.raid_helper.schemas.raid_helper import RaidHelperEventLinkRead


class CalendarSquadRead(BaseModel):
    id: int
    name: str
    slug: str


class FleetEventRead(BaseModel):
    id: int
    title: str
    category: str
    description: str | None = None
    location: str | None = None
    start_at: datetime
    end_at: datetime
    all_day: bool
    owner_id: int
    owner: UserReferenceRead
    squad_id: int | None = None
    squad: CalendarSquadRead | None = None
    scope_type: str = "fleet"
    scope_name: str = "Fleet"
    can_manage: bool = False
    is_cancelled: bool
    raid_helper_enabled: bool = True
    raid_helper_links: list[RaidHelperEventLinkRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
