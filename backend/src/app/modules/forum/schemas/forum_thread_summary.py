from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


from app.modules.accounts.schemas.user_reference_read import UserReferenceRead

class ForumThreadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    owner_id: int
    owner: UserReferenceRead
    reply_count: int
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime
