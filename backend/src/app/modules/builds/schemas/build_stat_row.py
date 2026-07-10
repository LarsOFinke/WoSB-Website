from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.ships.schemas.ship import ShipRead

class BuildStatRow(BaseModel):
    key: str
    label: str
    category: str
    base: int | float | None = None
    modifier: int | float | None = None
    effective: int | float | None = None
    unit: str | None = None
    precision: int = 0
    modifier_kind: str = "flat"
    effect_key: str | None = None
    is_debuff: bool = False
    source: str | None = None
