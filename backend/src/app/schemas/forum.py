from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constants import normalize_forum_category

from app.schemas.auth import UserRead
from app.schemas.file_asset import FileRead


class ForumPostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)
    file_ids: list[int] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def normalize(self) -> "ForumPostCreate":
        self.body = self.body.strip()
        self.file_ids = list(dict.fromkeys(int(file_id) for file_id in self.file_ids if int(file_id) > 0))
        return self


class ForumThreadCreate(ForumPostCreate):
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(default="general", max_length=80)

    @model_validator(mode="after")
    def normalize_thread(self) -> "ForumThreadCreate":
        self.title = self.title.strip()
        self.category = normalize_forum_category(self.category)
        return self


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


class ForumThreadRead(ForumThreadSummary):
    posts: list[ForumPostRead] = Field(default_factory=list)
