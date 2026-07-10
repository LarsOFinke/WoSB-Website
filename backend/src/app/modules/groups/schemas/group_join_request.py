from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.groups.models.group import GROUP_FOCUS_VALUES
from app.modules.ships.schemas.ship import ShipRead
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.builds.schemas.build_read import BuildRead

from app.modules.groups.schemas.group_member_base import GroupMemberBase

class GroupJoinRequest(GroupMemberBase):
    pass
