from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

FLEET_FOCUS_VALUES = {
    "trade",
    "faction",
    "port_battle",
    "training",
    "farming",
    "recon",
    "support",
    "mixed",
}
FLEET_ROLE_VALUES = {"member", "fleet_lieutenant", "fleet_admiral"}
FLEET_STATUS_VALUES = {"pending", "active", "inactive"}


class FleetBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=120)
    focus: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    standing_orders: str | None = Field(default=None, max_length=3000)
    sort_order: int = Field(default=100, ge=0, le=9999)
    is_active: bool = True

    @model_validator(mode="after")
    def normalize(self) -> "FleetBase":
        self.name = self.name.strip()
        self.slug = self.slug.strip().lower().replace(" ", "-")
        self.focus = self.focus.strip()
        if self.focus not in FLEET_FOCUS_VALUES:
            raise ValueError("Invalid fleet focus.")
        if isinstance(self.description, str):
            self.description = self.description.strip() or None
        if isinstance(self.standing_orders, str):
            self.standing_orders = self.standing_orders.strip() or None
        return self


class FleetCreate(FleetBase):
    pass


class FleetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    focus: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    standing_orders: str | None = Field(default=None, max_length=3000)
    sort_order: int | None = Field(default=None, ge=0, le=9999)
    is_active: bool | None = None

    @model_validator(mode="after")
    def normalize(self) -> "FleetUpdate":
        if isinstance(self.name, str):
            self.name = self.name.strip()
        if isinstance(self.slug, str):
            self.slug = self.slug.strip().lower().replace(" ", "-")
        if isinstance(self.focus, str):
            self.focus = self.focus.strip()
            if self.focus not in FLEET_FOCUS_VALUES:
                raise ValueError("Invalid fleet focus.")
        if isinstance(self.description, str):
            self.description = self.description.strip() or None
        if isinstance(self.standing_orders, str):
            self.standing_orders = self.standing_orders.strip() or None
        return self


class FleetMembershipUpdate(BaseModel):
    role: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, max_length=40)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "FleetMembershipUpdate":
        if isinstance(self.role, str):
            self.role = self.role.strip()
            if self.role not in FLEET_ROLE_VALUES:
                raise ValueError("Invalid fleet role.")
        if isinstance(self.status, str):
            self.status = self.status.strip()
            if self.status not in FLEET_STATUS_VALUES:
                raise ValueError("Invalid membership status.")
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self


class FleetJoinRequest(BaseModel):
    fleet_id: int
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "FleetJoinRequest":
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self


class FleetMemberUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    role: str


class FleetMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fleet_id: int
    user_id: int
    role: str
    status: str
    note: str | None = None
    joined_at: datetime
    updated_at: datetime
    user: FleetMemberUserRead


class FleetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    focus: str
    description: str | None = None
    standing_orders: str | None = None
    sort_order: int
    is_active: bool
    active_members_count: int = 0
    pending_members_count: int = 0
    leaders: list[FleetMembershipRead] = []
    created_at: datetime
    updated_at: datetime


class FleetDetail(FleetRead):
    memberships: list[FleetMembershipRead] = []


class FleetMembershipFleetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    focus: str
    is_active: bool


class FleetMembershipSelfRead(FleetMembershipRead):
    fleet: FleetMembershipFleetRead
