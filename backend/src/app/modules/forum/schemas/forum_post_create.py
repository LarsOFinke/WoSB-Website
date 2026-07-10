from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constants import normalize_forum_category

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.files.schemas.file_asset import FileRead

class ForumPostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)
    file_ids: list[int] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def normalize(self) -> "ForumPostCreate":
        self.body = self.body.strip()
        self.file_ids = list(dict.fromkeys(int(file_id) for file_id in self.file_ids if int(file_id) > 0))
        return self
