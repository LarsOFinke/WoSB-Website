from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ShipRead(BaseModel):
    id: int
    name: str
    rate: str
    progression_class: str
    ship_class: str
    school: str | None = None
    is_legend: bool
    is_premium: bool
    is_early_access: bool
    durability: int | None = None
    speed: Decimal | None = None
    agility: int | None = None
    armor: Decimal | None = None
    hold_capacity: int | None = None
    crew: int | None = None
    hull_size: str | None = None
    displacement_tons: int | None = None
    source_url: str | None = None
    source_note: str | None = None

    model_config = ConfigDict(from_attributes=True)
