from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    main_role: str | None = Field(default=None, max_length=80)
    fleet: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    preferred_ship_id: int | None = None
