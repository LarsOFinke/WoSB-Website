from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.ships.schemas.ship import ShipRead

from app.modules.builds.schemas.ship_stats import ShipStats
from app.modules.builds.schemas.build_base import BuildBase

class BuildRead(BuildBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None = None
    is_official_template: bool = False
    ship: ShipRead
    ship_stats: ShipStats
    created_at: datetime
    updated_at: datetime
