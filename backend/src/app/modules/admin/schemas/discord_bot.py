from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DiscordBotOperation = Literal["refresh", "install", "update", "start", "stop", "restart"]


class DiscordBotRequest(BaseModel):
    operation: DiscordBotOperation


class DiscordBotStatus(BaseModel):
    state: str = "idle"
    operation: str = "status"
    message: str = "Discord bot management has not been configured yet."
    configured: bool = False
    installed: bool = False
    service_state: str = "unknown"
    version: str | None = None
    commit: str | None = None
    requested_by: str | None = None
    requested_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    log_tail: list[str] = Field(default_factory=list)
    request_available: bool = False


class DiscordBotRequestResult(BaseModel):
    accepted: bool
    status: DiscordBotStatus
