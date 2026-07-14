from __future__ import annotations

import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator


DiscordBotOperation = Literal["refresh", "install", "update", "start", "stop", "restart"]
CHANNEL_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
CHANNEL_ID_PATTERN = re.compile(r"^[0-9]{15,22}$")


class DiscordBotRequest(BaseModel):
    operation: DiscordBotOperation


class DiscordBotConfigurationStatus(BaseModel):
    ready: bool = False
    env_file_present: bool = False
    config_file_present: bool = False
    discord_token_configured: bool = False
    webhook_secret_configured: bool = False
    management_token_configured: bool = False
    website_base_url: str = "https://royal-blackwater-fleet.eu"
    channels: dict[str, str] = Field(default_factory=dict)
    suppress_notifications: bool = False
    timestamp_tolerance_seconds: int = 300
    request_timeout_seconds: float = 15
    max_attempts: int = 3
    bind_host: str = "0.0.0.0"
    listen_port: int = 8765
    firewall_mode: str = "auto"
    public_webhook_path: str = "/webhooks/rbf"
    updated_at: str | None = None
    valid: bool = False
    message: str | None = None


class DiscordBotConfigurationUpdate(BaseModel):
    discord_bot_token: str | None = Field(default=None, min_length=20, max_length=256)
    webhook_secret: str | None = Field(default=None, min_length=32, max_length=512)
    website_base_url: str = Field(min_length=8, max_length=500)
    channels: dict[str, str]
    suppress_notifications: bool = False
    timestamp_tolerance_seconds: int = Field(default=300, ge=30, le=3600)
    request_timeout_seconds: float = Field(default=15, gt=0, le=120)
    max_attempts: int = Field(default=3, ge=1, le=8)
    restart_after_save: bool = True

    @field_validator("discord_bot_token", "webhook_secret", mode="before")
    @classmethod
    def normalize_optional_secret(cls, value: object) -> object:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("discord_bot_token", "webhook_secret")
    @classmethod
    def validate_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if any(character.isspace() for character in value) or "#" in value or value.startswith("CHANGE_ME"):
            raise ValueError("Secret values must be non-placeholder values without whitespace or '#'.")
        return value

    @field_validator("website_base_url")
    @classmethod
    def validate_website_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        parsed = urlsplit(normalized)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("website_base_url must be an absolute HTTPS URL.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
            raise ValueError("website_base_url must be an HTTPS origin without credentials, path, query or fragment.")
        return normalized

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for raw_key, raw_channel_id in value.items():
            key = str(raw_key).strip().lower()
            channel_id = str(raw_channel_id).strip()
            if not CHANNEL_KEY_PATTERN.fullmatch(key):
                raise ValueError(f"Invalid channel key: {key!r}.")
            if not CHANNEL_ID_PATTERN.fullmatch(channel_id):
                raise ValueError(f"Invalid Discord channel ID for {key!r}.")
            cleaned[key] = channel_id
        if "default" not in cleaned:
            raise ValueError("A default Discord channel is required.")
        return cleaned

    @model_validator(mode="after")
    def require_core_channels(self) -> "DiscordBotConfigurationUpdate":
        missing = {"events", "guides", "builds", "forum", "default"} - set(self.channels)
        if missing:
            raise ValueError(f"Missing required channel mappings: {', '.join(sorted(missing))}.")
        return self


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
    configuration: DiscordBotConfigurationStatus = Field(default_factory=DiscordBotConfigurationStatus)


class DiscordBotRequestResult(BaseModel):
    accepted: bool
    status: DiscordBotStatus
