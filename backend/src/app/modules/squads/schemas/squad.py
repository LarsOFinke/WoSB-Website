from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.modules.squads.models.squad_member import SQUAD_ROLES


class SquadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=3000)
    focus: str | None = Field(default=None, max_length=160)
    max_members: int | None = Field(default=None, ge=2, le=200)
    leader_membership_id: int

    @model_validator(mode="after")
    def normalize(self) -> "SquadCreate":
        self.name = self.name.strip()
        if isinstance(self.description, str):
            self.description = self.description.strip() or None
        if isinstance(self.focus, str):
            self.focus = self.focus.strip() or None
        return self


class SquadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=3000)
    focus: str | None = Field(default=None, max_length=160)
    max_members: int | None = Field(default=None, ge=2, le=200)

    @model_validator(mode="after")
    def normalize(self) -> "SquadUpdate":
        if isinstance(self.name, str):
            self.name = self.name.strip()
        if isinstance(self.description, str):
            self.description = self.description.strip() or None
        if isinstance(self.focus, str):
            self.focus = self.focus.strip() or None
        return self


class SquadMemberCreate(BaseModel):
    fleet_membership_id: int
    role: str = "member"
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "SquadMemberCreate":
        self.role = self.role.strip().lower()
        if self.role not in SQUAD_ROLES:
            raise ValueError("Invalid squad role.")
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self


class SquadMemberUpdate(BaseModel):
    role: str | None = None
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "SquadMemberUpdate":
        if isinstance(self.role, str):
            self.role = self.role.strip().lower()
            if self.role not in SQUAD_ROLES:
                raise ValueError("Invalid squad role.")
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self


class SquadMemberRead(BaseModel):
    id: int
    fleet_membership_id: int
    user_id: int
    display_name: str
    fleet_role: str
    squad_role: str
    note: str | None = None
    joined_at: datetime


class SquadRosterMemberRead(BaseModel):
    fleet_membership_id: int
    user_id: int
    display_name: str
    fleet_role: str
    squad_ids: list[int] = Field(default_factory=list)


class SquadSummaryRead(BaseModel):
    id: int
    fleet_id: int
    name: str
    slug: str
    description: str | None = None
    focus: str | None = None
    max_members: int | None = None
    is_active: bool
    leader: SquadMemberRead | None = None
    member_count: int
    is_member: bool
    can_manage: bool
    can_administer: bool
    created_at: datetime
    updated_at: datetime


class SquadDetailRead(SquadSummaryRead):
    members: list[SquadMemberRead] = Field(default_factory=list)
