from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.builds.schemas.inventory_slot import InventorySlot
from app.modules.ships.schemas.ship import ShipRead


class BuildListMetrics(BaseModel):
    crew_total: int = 0
    crew_capacity: int = 0
    upgrade_slots_used: int = 0
    upgrade_slots_available: int = 0
    weapon_total: int = 0
    special_crew_total: int = 0
    ammunition_slots_used: int = 0
    consumable_slots_used: int = 0
    hold_slots_used: int = 0


class BuildSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None = None
    is_official_template: bool = False
    build_name: str
    build_type: str
    classification_tags: list[str] = Field(default_factory=list)
    build_role_label: str
    upvote_count: int = 0
    has_upvoted: bool = False
    ship: ShipRead
    metrics: BuildListMetrics
    ammunition_slots: list[InventorySlot] = Field(default_factory=list)
    hold_slots: list[InventorySlot] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BuildPage(BaseModel):
    items: list[BuildSummaryRead] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
