from __future__ import annotations


from pydantic import BaseModel, Field, model_validator


class InventorySlot(BaseModel):
    item: str = Field(min_length=1, max_length=160)
    quantity: int = Field(default=1, ge=1, le=999_999)

    @model_validator(mode="after")
    def normalize_item(self) -> "InventorySlot":
        self.item = self.item.strip()
        return self
