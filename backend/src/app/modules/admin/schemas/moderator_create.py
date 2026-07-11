from __future__ import annotations
from app.core.password_policy import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


from pydantic import BaseModel, Field, model_validator


class ModeratorCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    display_name: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "ModeratorCreate":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        return self
