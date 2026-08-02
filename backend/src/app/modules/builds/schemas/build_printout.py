from datetime import datetime

from pydantic import BaseModel


class BuildPrintoutRead(BaseModel):
    url: str
    checksum: str
    size_bytes: int
    updated_at: datetime
    changed: bool
