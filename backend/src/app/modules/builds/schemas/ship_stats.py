from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.builds.schemas.build_stat_row import BuildStatRow

class ShipStats(BaseModel):
    crew_total: int
    crew_capacity: int
    crew_remaining: int
    sailor_minimum: int
    sailors_required_met: bool
    sailor_target: int | None = None
    base_sailor_target: int | None = None
    effective_sailor_target: int | None = None
    sailing_efficiency_pct: int = 100
    upgrade_slots_used: int
    upgrade_slots_available: int
    base_upgrade_slots_available: int | None = None
    extra_upgrade_slots: int = 0
    expansion_upgrade_slots: int = 0
    research_upgrade_slots: int = 0
    ship_extra_upgrade_slots: int = 0
    upgrade_slot_5_unlocked: bool = False
    upgrade_slot_6_available: bool = False
    upgrade_slot_6_unlocked: bool = False
    upgrade_slot_7_available: bool = False
    base_crew_capacity: int | None = None
    effective_crew_capacity: int | None = None
    base_sailor_minimum: int | None = None
    effective_sailor_minimum: int | None = None
    item_effects: dict[str, int | float] = Field(default_factory=dict)
    sail_effects: dict[str, int | float] = Field(default_factory=dict)
    lantern_effects: dict[str, int | float] = Field(default_factory=dict)
    upgrade_effects: dict[str, int | float] = Field(default_factory=dict)
    special_crew_effects: dict[str, int | float] = Field(default_factory=dict)
    research_upgrade_slot_effects: dict[str, int | float] = Field(default_factory=dict)
    upgrade_buffs: dict[str, int | float] = Field(default_factory=dict)
    upgrade_debuffs: dict[str, int | float] = Field(default_factory=dict)
    base_stats: dict[str, int | float | str | None] = Field(default_factory=dict)
    effective_stats: dict[str, int | float | None] = Field(default_factory=dict)
    stat_rows: list[BuildStatRow] = Field(default_factory=list)
    stat_warnings: list[str] = Field(default_factory=list)
    weapon_slots: dict[str, int]
    weapon_capacity: dict[str, int] = Field(default_factory=dict)
    weapon_total: int
    weapon_capacity_total: int = 0
    special_crew_total: int
    inventory_slots_used: int
    ammunition_slots_used: int
    consumable_slots_used: int
    hold_slots_used: int
