from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.files.schemas.file_asset import FileRead

class GuideCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    category: str = Field(default="general", max_length=80)
    summary: str | None = Field(default=None, max_length=400)
    body: str = Field(min_length=1, max_length=20000)
    file_ids: list[int] = Field(default_factory=list, max_length=20)
    build_ids: list[int] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def normalize(self) -> "GuideCreate":
        self.title = self.title.strip()
        self.category = self.category.strip().lower() or "general"
        self.body = self.body.strip()
        if isinstance(self.summary, str):
            self.summary = self.summary.strip() or None
        self.file_ids = list(dict.fromkeys(int(file_id) for file_id in self.file_ids if int(file_id) > 0))
        self.build_ids = list(dict.fromkeys(int(build_id) for build_id in self.build_ids if int(build_id) > 0))
        return self
