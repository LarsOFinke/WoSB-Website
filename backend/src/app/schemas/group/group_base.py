from datetime import datetime

from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=2000)
    focus: str = Field(default="pve_general", max_length=40)
    ship_id: int | None = None
    ship_class: str | None = Field(default=None, max_length=80)
    max_members: int = Field(default=8, ge=2, le=50)
    min_ship_rate: int | None = Field(default=None, ge=1, le=7)
    allow_anonymous: bool = True
    fleet_restriction: str | None = Field(default=None, max_length=120)
    scheduled_at: datetime | None = None
