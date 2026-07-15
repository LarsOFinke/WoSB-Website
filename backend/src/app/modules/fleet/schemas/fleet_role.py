from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ROLE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,39}$")


class FleetRoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    label: str = Field(min_length=2, max_length=80)
    rank: int = Field(ge=1, le=79)
    is_leadership: bool = False
    can_manage_fleet: bool = False
    can_manage_members: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        code = value.strip().lower().replace("-", "_").replace(" ", "_")
        if not ROLE_CODE_PATTERN.fullmatch(code):
            raise ValueError("Role code must use lowercase letters, numbers and underscores.")
        return code

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def normalize_permissions(self) -> "FleetRoleCreate":
        if self.can_manage_fleet or self.can_manage_members:
            self.is_leadership = True
        return self


class FleetRoleUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=80)
    rank: int | None = Field(default=None, ge=1, le=79)
    is_leadership: bool | None = None
    can_manage_fleet: bool | None = None
    can_manage_members: bool | None = None
    is_active: bool | None = None

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else None


class FleetRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label: str
    rank: int
    is_leadership: bool
    can_manage_fleet: bool
    can_manage_members: bool
    is_system: bool
    is_active: bool
    member_count: int = 0
