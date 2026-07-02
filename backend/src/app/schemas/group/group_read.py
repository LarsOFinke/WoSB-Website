from datetime import datetime

from pydantic import BaseModel

from app.schemas.group.group_participant_read import GroupParticipantRead


class GroupRead(BaseModel):
    id: int
    owner_id: int
    owner_name: str | None = None
    title: str
    description: str
    focus: str
    focus_label: str
    ship_id: int | None = None
    ship_name: str | None = None
    ship_class: str
    rate: str | None = None
    max_members: int
    min_ship_rate: int | None = None
    allow_anonymous: bool
    fleet_restriction: str | None = None
    scheduled_at: datetime | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    closed_at: datetime | None = None
    archived_at: datetime | None = None
    status: str
    status_label: str
    active: bool
    members: list[str]
    waiting_list: list[str]
    participants: list[GroupParticipantRead]
    participant_count: int
    free_slots: int
    is_full: bool
    is_joined: bool = False
    can_join: bool = False
    can_join_reason: str | None = None
    can_manage: bool = False
    guest_join_token: str | None = None
