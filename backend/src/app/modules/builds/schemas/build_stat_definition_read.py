from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class BuildStatDefinitionRead(BaseModel):
    key: str
    label: str
    category: str
    base_field: str | None = None
    unit: str | None = None
    pct_effect: str | None = None
    flat_effect: str | None = None
    precision: int = 0
    positive_is_good: bool = True
    source: str | None = None
