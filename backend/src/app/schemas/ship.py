from pydantic import BaseModel, ConfigDict


class ShipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rate: int
    ship_type: str
    crew_capacity: int
    sailor_minimum: int
    sail_slots: int
    upgrade_slots: int
    has_lantern: bool
    is_active: bool
