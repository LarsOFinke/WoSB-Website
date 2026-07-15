from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WebhookDeliveryStatus = Literal["queued", "success", "failed"]
WebhookDeliveryMode = Literal["signed_json", "discord"]
WebhookScopeType = Literal["global", "fleet", "squad"]


class OutboundWebhookInput(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    endpoint_url: str | None = Field(default=None, min_length=8, max_length=1000)
    event_types: list[str] = Field(min_length=1, max_length=64)
    delivery_mode: WebhookDeliveryMode = "signed_json"
    scope_type: WebhookScopeType = "global"
    scope_id: int | None = Field(default=None, ge=1)
    channel_key: str | None = Field(default=None, max_length=120)
    message_template: str | None = Field(default=None, max_length=4000)
    discord_username: str | None = Field(default=None, max_length=80)
    discord_avatar_url: str | None = Field(default=None, max_length=1000)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("endpoint_url")
    @classmethod
    def strip_endpoint(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else None

    @field_validator(
        "channel_key", "message_template", "discord_username", "discord_avatar_url"
    )
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
        if self.delivery_mode != "discord":
            self.discord_username = None
            self.discord_avatar_url = None
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
    delivery_mode: WebhookDeliveryMode
    scope_type: WebhookScopeType
    scope_id: int | None = None
    channel_key: str | None = None
    message_template: str | None = None
    discord_username: str | None = None
    discord_avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_username: str
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    secret_hint: str
    signing_secret: str | None = None


class OutboundWebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    webhook_id: int
    webhook_name: str
    delivery_mode: WebhookDeliveryMode = "signed_json"
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


class OutboundWebhookEventCatalogItem(BaseModel):
    key: str
    group: str
    description: str
    default_template: str


class OutboundWebhookSummary(BaseModel):
    total: int = 0
    active: int = 0
    failing: int = 0
    discord: int = 0
    signed_json: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
