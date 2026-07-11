from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


from app.modules.accounts.schemas.user_read import UserRead

class ForumThreadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    owner_id: int
    owner: UserRead
    reply_count: int
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime
