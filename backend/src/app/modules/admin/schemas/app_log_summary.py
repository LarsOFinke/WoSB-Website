from __future__ import annotations


from pydantic import BaseModel


class AppLogSummary(BaseModel):
    total: int
    errors: int
    warnings: int
    slow_requests: int
    recent_status: dict[str, int]
