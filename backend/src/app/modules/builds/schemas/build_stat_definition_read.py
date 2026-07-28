from __future__ import annotations

from pydantic import BaseModel


class BuildStatDefinitionRead(BaseModel):
    key: str
    label: str
    category: str
    base_field: str | None = None
    unit: str | None = None
    pct_effect: str | None = None
    flat_effect: str | None = None
    calculation_flat_effect: str | None = None
    precision: int = 0
    positive_is_good: bool = True
    source: str | None = None
    pct_base_field: str | None = None
