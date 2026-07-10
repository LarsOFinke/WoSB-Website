from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.fleet.schemas.fleet_read import FleetRead

class AppLogSummary(BaseModel):
    total: int
    errors: int
    warnings: int
    slow_requests: int
    recent_status: dict[str, int]
