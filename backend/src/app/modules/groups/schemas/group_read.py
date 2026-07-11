from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field

from app.modules.accounts.schemas.user_read import UserRead

from app.modules.groups.schemas.group_member_read import GroupMemberRead
from app.modules.groups.schemas.group_base import GroupBase

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
