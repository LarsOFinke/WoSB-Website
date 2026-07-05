from pydantic import BaseModel, Field, model_validator

from app.schemas.auth import UserRead


class ModeratorCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "ModeratorCreate":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        return self


class ModeratorCreateResponse(BaseModel):
    user: UserRead
