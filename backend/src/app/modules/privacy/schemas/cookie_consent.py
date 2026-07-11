from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CookieConsentChoice(BaseModel):
    necessary: bool = True
    preferences: bool = False
    analytics: bool = False
    external_media: bool = False

    @field_validator("necessary")
    @classmethod
    def necessary_cannot_be_disabled(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Strictly necessary cookies cannot be disabled.")
        return True


class CookieConsentRead(CookieConsentChoice):
    has_decision: bool = False
    policy_version: str
    decided_at: datetime | None = None


class CookieConsentPolicy(BaseModel):
    version: str
    categories: tuple[str, ...] = Field(
        default=("necessary", "preferences", "analytics", "external_media")
    )
