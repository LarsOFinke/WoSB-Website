from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from app.core.site_role import SiteRole


class UserAdministrationUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {role.value for role in SiteRole}:
            raise ValueError("Invalid site role.")
        return normalized

    @model_validator(mode="after")
    def require_change(self) -> "UserAdministrationUpdate":
        if self.role is None and self.is_active is None:
            raise ValueError("At least one account change is required.")
        return self
