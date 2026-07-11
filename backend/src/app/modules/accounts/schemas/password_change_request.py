from __future__ import annotations
from app.core.password_policy import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


from pydantic import BaseModel, Field, model_validator

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @model_validator(mode="after")
    def validate_new_password(self) -> "PasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from the current password.")
        return self
