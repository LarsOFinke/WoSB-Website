from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.accounts.schemas.user_reference_read import UserReferenceRead

class GuideSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    summary: str | None = None
    owner_id: int
    owner: UserReferenceRead
    attachment_count: int = 0
    build_reference_count: int = 0
    created_at: datetime
    updated_at: datetime
