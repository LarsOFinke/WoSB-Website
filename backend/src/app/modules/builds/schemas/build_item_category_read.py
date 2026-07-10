from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class BuildItemCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    label: str
    sort_order: int
