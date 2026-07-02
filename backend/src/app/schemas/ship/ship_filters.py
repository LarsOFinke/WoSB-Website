from pydantic import BaseModel


class ShipFilters(BaseModel):
    rate: str | None = None
    progression_class: str | None = None
    ship_class: str | None = None
    search: str | None = None
