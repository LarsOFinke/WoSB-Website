from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserReferenceRead(BaseModel):
    """Minimal identity embedded in shared content responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
