from __future__ import annotations

from pydantic import BaseModel, Field


class FleetMembershipManagementRead(BaseModel):
    can_edit_directory: bool = False
    can_change_role: bool = False
    can_change_status: bool = False
    assignable_roles: list[str] = Field(default_factory=list)
    protected: bool = True
    reason: str | None = "insufficient"
