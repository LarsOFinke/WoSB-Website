from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.modules.accounts.schemas.user_reference_read import UserReferenceRead


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
    can_manage: bool = False
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime
