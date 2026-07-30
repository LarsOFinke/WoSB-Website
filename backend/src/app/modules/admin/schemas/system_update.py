from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


SystemUpdateOperation = Literal[
    "restart",
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
    requested_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    request_available: bool = False


class SystemUpdateRequestResult(BaseModel):
    accepted: bool
    status: SystemUpdateStatus
