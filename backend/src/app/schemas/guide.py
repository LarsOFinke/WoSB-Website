from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.auth import UserRead
from app.schemas.file_asset import FileRead


class GuideCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    category: str = Field(default="general", max_length=80)
    summary: str | None = Field(default=None, max_length=400)
    body: str = Field(min_length=1, max_length=20000)
    file_ids: list[int] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def normalize(self) -> "GuideCreate":
        self.title = self.title.strip()
        self.category = self.category.strip().lower() or "general"
        self.body = self.body.strip()
        if isinstance(self.summary, str):
            self.summary = self.summary.strip() or None
        self.file_ids = list(dict.fromkeys(int(file_id) for file_id in self.file_ids if int(file_id) > 0))
        return self


class GuideSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    summary: str | None = None
    owner_id: int
    owner: UserRead
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime


class GuideRead(GuideSummary):
    body: str
    attachments: list[FileRead] = Field(default_factory=list)
