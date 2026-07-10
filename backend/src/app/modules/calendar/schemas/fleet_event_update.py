from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.user_read import UserRead

from app.modules.calendar.schemas.fleet_event_create import FleetEventCreate

class FleetEventUpdate(FleetEventCreate):
    pass
