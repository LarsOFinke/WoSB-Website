from __future__ import annotations


from pydantic import BaseModel, ConfigDict

class FleetMembershipFleetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    focus: str
    is_active: bool
