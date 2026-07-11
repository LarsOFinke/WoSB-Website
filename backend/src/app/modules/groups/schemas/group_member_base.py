from __future__ import annotations


from pydantic import BaseModel, Field, model_validator


class GroupMemberBase(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    ship_id: int | None = None
    build_id: int | None = None
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
