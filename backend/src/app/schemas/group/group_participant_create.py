from pydantic import BaseModel, Field


class GroupParticipantCreate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    fleet_name: str | None = Field(default=None, max_length=120)
    participant_role: str | None = Field(default=None, max_length=40)
    ship_id: int | None = None
    custom_ship_name: str | None = Field(default=None, max_length=120)
    custom_ship_rate: int | None = Field(default=None, ge=1, le=7)
    note: str | None = Field(default=None, max_length=1000)
