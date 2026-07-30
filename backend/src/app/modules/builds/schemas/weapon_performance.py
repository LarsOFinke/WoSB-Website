from pydantic import BaseModel, ConfigDict, Field


class WeaponPerformanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_damage: float = Field(ge=0)
    reload_seconds: float = Field(gt=0)
