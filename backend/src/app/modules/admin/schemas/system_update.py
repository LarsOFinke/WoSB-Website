from __future__ import annotations

from pydantic import BaseModel, Field


class SystemUpdateStatus(BaseModel):
    state: str = "idle"
    message: str = "No update has been requested yet."
    requested_by: str | None = None
    requested_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    commit_before: str | None = None
    commit_after: str | None = None
    log_tail: list[str] = Field(default_factory=list)
    request_available: bool = False


class SystemUpdateRequestResult(BaseModel):
    accepted: bool
    status: SystemUpdateStatus
