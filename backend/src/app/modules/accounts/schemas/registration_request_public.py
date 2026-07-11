from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

class RegistrationRequestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    status: str
    created_at: datetime
