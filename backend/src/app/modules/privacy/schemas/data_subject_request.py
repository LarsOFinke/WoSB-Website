from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DataSubjectRequestCreate(BaseModel):
    request_type: Literal["correction", "deletion"]
    details: str | None = Field(default=None, max_length=4000)
    confirmation: str | None = Field(default=None, max_length=80)


class DataSubjectRequestResolve(BaseModel):
    decision: Literal["complete", "reject"]
    resolution_note: str = Field(min_length=3, max_length=4000)


class DataSubjectRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_user_id: int
    subject_username: str
    request_type: str
    status: str
    details: str | None
    resolution_note: str | None
    handled_by_user_id: int | None
    created_at: datetime
    resolved_at: datetime | None
