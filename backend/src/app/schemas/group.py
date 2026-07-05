from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.group import GROUP_FOCUS_VALUES
from app.schemas.ship import ShipRead
from app.schemas.auth import UserRead


class GroupMemberBase(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    ship_id: int | None = None
    ship_name: str | None = Field(default=None, max_length=140)
    ship_rate: int | None = Field(default=None, ge=1, le=7)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize_member_strings(self) -> "GroupMemberBase":
        for field_name in ("display_name", "fleet_name", "ship_name", "note"):
            value = getattr(self, field_name)
            if isinstance(value, str):
                stripped = value.strip()
                setattr(self, field_name, stripped or None)
        return self


class GroupJoinRequest(GroupMemberBase):
    pass


class GroupMemberRead(GroupMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    is_guest: bool
    is_active: bool
    joined_at: datetime
    left_at: datetime | None = None
    ship: ShipRead | None = None


class GroupBase(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    focus: str = Field(default="pve_general", max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    max_members: int = Field(default=5, ge=2, le=50)
    min_ship_rate: int | None = Field(default=None, ge=1, le=7)
    max_ship_rate: int | None = Field(default=None, ge=1, le=7)
    allow_guests: bool = True
    fleet_restriction: str | None = Field(default=None, max_length=120)

    @field_validator("focus")
    @classmethod
    def validate_focus(cls, value: str) -> str:
        normalized = value.strip().lower() if isinstance(value, str) else "pve_general"
        if normalized not in GROUP_FOCUS_VALUES:
            raise ValueError("Invalid group focus.")
        return normalized

    @model_validator(mode="after")
    def normalize_strings(self) -> "GroupBase":
        if self.min_ship_rate is not None and self.max_ship_rate is not None and self.max_ship_rate > self.min_ship_rate:
            raise ValueError("Maximum rate must be numerically lower than or equal to minimum rate.")
        for field_name in ("title", "description", "fleet_restriction"):
            value = getattr(self, field_name)
            if isinstance(value, str):
                stripped = value.strip()
                setattr(self, field_name, stripped or None)
        return self


class GroupCreate(GroupBase):
    pass


class GroupRead(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    closed_at: datetime | None = None
    owner: UserRead
    members: list[GroupMemberRead] = Field(default_factory=list)
    active_members_count: int
    spots_left: int
    is_joinable: bool
