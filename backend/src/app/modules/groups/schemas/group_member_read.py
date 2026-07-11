from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict

from app.modules.ships.schemas.ship import ShipRead
from app.modules.builds.schemas.build_read import BuildRead

from app.modules.groups.schemas.group_member_base import GroupMemberBase

class GroupMemberRead(GroupMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    is_guest: bool
    is_active: bool
    joined_at: datetime
    left_at: datetime | None = None
    ship: ShipRead | None = None
    build: BuildRead | None = None
