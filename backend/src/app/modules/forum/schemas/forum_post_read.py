from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


from app.modules.accounts.schemas.user_read import UserRead
from app.modules.files.schemas.file_asset import FileRead

class ForumPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: int
    author_id: int
    author: UserRead
    body: str
    attachments: list[FileRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
