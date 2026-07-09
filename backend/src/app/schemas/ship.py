from pydantic import BaseModel, ConfigDict


class ShipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rate: int
    ship_type: str
    durability: int
    speed_knots: float
    maneuverability: float
    armor: float
    hold_capacity: int
    crew_capacity: int
    sailor_minimum: int
    weapon_layout: str | None = None
    displacement_tons: int
    source: str | None = None
    sail_slots: int
    upgrade_slots: int
    has_lantern: bool
    is_active: bool
