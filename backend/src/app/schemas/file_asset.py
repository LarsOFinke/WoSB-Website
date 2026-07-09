from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None = None
    original_name: str
    stored_name: str
    relative_path: str
    public_url: str
    mime_type: str
    size_bytes: int
    usage_context: str
    created_at: datetime
