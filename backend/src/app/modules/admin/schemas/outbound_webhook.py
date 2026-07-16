from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WebhookDeliveryStatus = Literal["queued", "success", "failed"]
WebhookScopeType = Literal["global", "fleet", "squad"]


class OutboundWebhookInput(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    endpoint_url: str | None = Field(default=None, min_length=8, max_length=1000)
    event_types: list[str] = Field(default_factory=list, max_length=64)
    scope_type: WebhookScopeType = "global"
    scope_id: int | None = Field(default=None, ge=1)
    message_template: str | None = Field(default=None, max_length=4000)
    discord_username: str | None = Field(default=None, max_length=80)
    discord_avatar_url: str | None = Field(default=None, max_length=1000)
    broadcast_enabled: bool = False
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("endpoint_url")
    @classmethod
    def strip_endpoint(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else None

    @field_validator("message_template", "discord_username", "discord_avatar_url")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("event_types")
    @classmethod
    def normalize_events(cls, value: list[str]) -> list[str]:
        return sorted({item.strip() for item in value if item.strip()})

    @model_validator(mode="after")
    def validate_scope(self) -> "OutboundWebhookInput":
        if self.scope_type == "global":
            self.scope_id = None
        elif self.scope_id is None:
            raise ValueError("A fleet or squad scope requires a scope ID.")
        if not self.event_types and not self.broadcast_enabled:
            raise ValueError("Select at least one event or enable this webhook for broadcasts.")
        return self


class OutboundWebhookCreate(OutboundWebhookInput):
    endpoint_url: str = Field(min_length=8, max_length=1000)


class OutboundWebhookUpdate(OutboundWebhookInput):
    pass


class OutboundWebhookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    endpoint_url: str
    event_types: list[str]
    scope_type: WebhookScopeType
    scope_id: int | None = None
    message_template: str | None = None
    discord_username: str | None = None
    discord_avatar_url: str | None = None
    broadcast_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_username: str
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None


class OutboundWebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    webhook_id: int
    webhook_name: str
    delivery_id: str
    event_type: str
    resource_type: str
    resource_id: str
    status: WebhookDeliveryStatus
    attempts: int
    response_status: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    created_at: datetime
    last_attempt_at: datetime | None = None
    delivered_at: datetime | None = None


class OutboundWebhookTestRequest(BaseModel):
    event_type: str = Field(default="integration.test", max_length=80)


class OutboundWebhookBroadcastRequest(BaseModel):
    webhook_ids: list[int] = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1, max_length=2000)
    discord_username: str | None = Field(default=None, max_length=80)
    discord_avatar_url: str | None = Field(default=None, max_length=1000)

    @field_validator("webhook_ids")
    @classmethod
    def normalize_webhook_ids(cls, value: list[int]) -> list[int]:
        normalized = sorted({int(item) for item in value if int(item) > 0})
        if not normalized:
            raise ValueError("Select at least one broadcast webhook.")
        return normalized

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Broadcast message must not be empty.")
        return stripped

    @field_validator("discord_username", "discord_avatar_url")
    @classmethod
    def strip_broadcast_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class OutboundWebhookEventCatalogItem(BaseModel):
    key: str
    group: str
    description: str
    default_template: str


class OutboundWebhookSummary(BaseModel):
    total: int = 0
    active: int = 0
    failing: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
