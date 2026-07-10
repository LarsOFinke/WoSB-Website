from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.files.schemas.file_asset import FileRead

from app.modules.guides.schemas.guide_summary import GuideSummary

class GuideRead(GuideSummary):
    body: str
    attachments: list[FileRead] = Field(default_factory=list)
    builds: list[BuildRead] = Field(default_factory=list)
