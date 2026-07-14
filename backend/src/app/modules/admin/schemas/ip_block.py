from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class IpBlockCreate(BaseModel):
    ip_address: str = Field(min_length=2, max_length=64)
    reason: str = Field(min_length=3, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)
    expires_at: datetime | None = None

    @field_validator("ip_address", "reason")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("notes")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("expires_at")
    @classmethod
    def normalize_expiration(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value


class IpBlockUnblock(BaseModel):
    reason: str | None = Field(default=None, max_length=240)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class IpBlockRead(BaseModel):
    id: int
    ip_address: str
    reason: str
    notes: str | None = None
    created_at: datetime
    created_by_user_id: int | None = None
    created_by_username: str
    expires_at: datetime | None = None
    unblocked_at: datetime | None = None
    unblocked_by_user_id: int | None = None
    unblocked_by_username: str | None = None
    unblock_reason: str | None = None
    is_active: bool
    is_temporary: bool
    is_expired: bool


class IpBlockSummary(BaseModel):
    total: int = 0
    active: int = 0
    permanent: int = 0
    temporary: int = 0
    expired: int = 0
    unblocked: int = 0
