from pydantic import BaseModel, ConfigDict


class ShipMortarModificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mortar_capacity: int
    max_caliber_inches: float
    broadside_capacity_delta: int
    durability_delta: int
    speed_pct: float
    maneuverability_delta: float
    hold_capacity_pct: float
    crew_capacity_delta: int
    source: str


class ShipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rate: int
    ship_type: str
    durability: int
    speed_min_knots: float
    speed_knots: float
    maneuverability: float
    armor: float
    hold_capacity: int
    crew_capacity: int
    sailor_minimum: int
    weapon_layout: str | None = None
    front_weapon_capacity: int = 0
    broadside_weapon_capacity: int = 0
    rear_weapon_capacity: int = 0
    mortar_weapon_capacity: int = 0
    special_weapon_capacity: int = 0
    front_special_weapon_capacity: int = 0
    rear_special_weapon_capacity: int = 0
    dedicated_special_weapon_capacity: int = 0
    max_mortar_caliber_inches: int | float | None = None
    mortar_modification: ShipMortarModificationRead | None = None
    displacement_tons: int
    source: str | None = None
    image_url: str | None = None
    sail_slots: int
    upgrade_slots: int
    has_lantern: bool
    is_active: bool
