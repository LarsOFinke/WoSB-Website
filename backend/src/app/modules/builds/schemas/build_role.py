from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

BUILD_ROLE_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


class BuildRoleBase(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=-10000, le=10000)

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class BuildRoleCreate(BuildRoleBase):
    slug: str = Field(min_length=1, max_length=32)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not BUILD_ROLE_SLUG_PATTERN.fullmatch(normalized):
            raise ValueError("Role slug may contain lowercase letters, numbers, hyphens and underscores.")
        return normalized


class BuildRoleUpdate(BuildRoleBase):
    pass


class BuildRoleRead(BuildRoleBase):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    created_at: datetime
    updated_at: datetime


class BuildRoleAssignment(BaseModel):
    build_type: str = Field(min_length=1, max_length=32)

    @field_validator("build_type")
    @classmethod
    def normalize_build_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not BUILD_ROLE_SLUG_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid build role.")
        return normalized
