from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SystemUpdateOperation = Literal[
    "update",
    "update_migrate",
    "update_migrate_seed",
    "update_migrate_seed_restore",
]


class SystemUpdateRequest(BaseModel):
    operation: SystemUpdateOperation = "update"


class SystemUpdateStatus(BaseModel):
    state: str = "idle"
    operation: str = "update"
    message: str = "No update has been requested yet."
    requested_by: str | None = None
    requested_at: str | None = None
    started_at: str | None = None
    heartbeat_at: str | None = None
    finished_at: str | None = None
    commit_before: str | None = None
    commit_after: str | None = None
    log_tail: list[str] = Field(default_factory=list)
    request_available: bool = False


class SystemUpdateRequestResult(BaseModel):
    accepted: bool
    status: SystemUpdateStatus
