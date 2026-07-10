from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.ships.schemas.ship import ShipRead

from app.modules.builds.schemas.build_base import BuildBase

class BuildCreate(BuildBase):
    pass
