from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PrivacyContactCreate(BaseModel):
    reply_email: str = Field(min_length=3, max_length=254)
    subject: str = Field(min_length=3, max_length=160)
    message: str = Field(min_length=10, max_length=4000)
    website: str = Field(default="", max_length=0, exclude=True)

    @field_validator("reply_email")
    @classmethod
    def validate_reply_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[1]:
            raise ValueError("Enter a valid reply email address.")
        return normalized


class PrivacyContactResolve(BaseModel):
    decision: Literal["complete", "reject"]
    resolution_note: str = Field(min_length=3, max_length=4000)


class PrivacyContactRead(BaseModel):
    id: int
    user_id: int | None
    reply_email: str
    subject: str
    message: str
    status: str
    resolution_note: str | None
    handled_by_user_id: int | None
    created_at: datetime
    resolved_at: datetime | None
