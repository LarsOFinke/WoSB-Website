from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.fleet.schemas.fleet_base import FleetBase

class FleetCreate(FleetBase):
    pass
