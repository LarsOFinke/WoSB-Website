from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RegisterRequest(BaseModel):
    """Account access request.

    Fleet applications are intentionally a separate authenticated workflow.
    Rejecting unknown fields prevents stale clients from coupling registration
    to fleet membership again.
    """

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "RegisterRequest":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        return self
