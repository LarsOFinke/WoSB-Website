from datetime import datetime

from pydantic import BaseModel


class GroupParticipantRead(BaseModel):
    id: int
    display_name: str
    status: str
    participant_role: str | None = None
    is_anonymous: bool = False
    fleet_name: str | None = None
    ship_id: int | None = None
    ship_name: str | None = None
    ship_rate: str | None = None
    custom_ship_name: str | None = None
    custom_ship_rate: int | None = None
    note: str | None = None
    active: bool = True
    joined_at: datetime | None = None
    left_at: datetime | None = None
    join_token: str | None = None
