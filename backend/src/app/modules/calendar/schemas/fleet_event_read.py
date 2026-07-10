from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead

class FleetEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    description: str | None = None
    location: str | None = None
    start_at: datetime
    end_at: datetime
    all_day: bool
    owner_id: int
    owner: UserRead
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime
