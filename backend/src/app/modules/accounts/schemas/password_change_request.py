from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=6, max_length=200)

    @model_validator(mode="after")
    def validate_new_password(self) -> "PasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from the current password.")
        return self
