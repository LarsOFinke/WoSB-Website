from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.files.schemas.file_asset import FileRead

class GuideSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    summary: str | None = None
    owner_id: int
    owner: UserRead
    attachment_count: int = 0
    build_reference_count: int = 0
    created_at: datetime
    updated_at: datetime
