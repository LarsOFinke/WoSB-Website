from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    actor_user_id: int | None = None
    actor_username: str
    actor_role: str
    entity_type: str
    entity_id: str
    action: str
    summary: str
    changed_fields: list[str] = Field(default_factory=list)
