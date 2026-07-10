from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.fleet.schemas.fleet_read import FleetRead

class AppLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    level: str
    logger: str
    message: str
    request_id: str | None = None
    method: str | None = None
    path: str | None = None
    status_code: int | None = None
    duration_ms: float | None = None
    client: str | None = None
    client_ip: str | None = None
    forwarded_for: str | None = None
    user_agent: str | None = None
    query_string: str | None = None
    exception: str | None = None
