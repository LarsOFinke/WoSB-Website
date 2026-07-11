from __future__ import annotations


from pydantic import BaseModel, Field, model_validator


class RegistrationDecision(BaseModel):
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "RegistrationDecision":
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self
