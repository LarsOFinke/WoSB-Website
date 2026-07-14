from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


WebhookDeliveryStatus = Literal["queued", "success", "failed"]


class OutboundWebhookCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    endpoint_url: str = Field(min_length=8, max_length=1000)
    event_types: list[str] = Field(min_length=1, max_length=32)
    channel_key: str | None = Field(default=None, max_length=120)
    message_template: str | None = Field(default=None, max_length=4000)
    is_active: bool = True

    @field_validator("name", "endpoint_url")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("channel_key", "message_template")
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


class OutboundWebhookUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    endpoint_url: str = Field(min_length=8, max_length=1000)
    event_types: list[str] = Field(min_length=1, max_length=32)
    channel_key: str | None = Field(default=None, max_length=120)
    message_template: str | None = Field(default=None, max_length=4000)
    is_active: bool = True

    @field_validator("name", "endpoint_url")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator("channel_key", "message_template")
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


class OutboundWebhookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    endpoint_url: str
    event_types: list[str]
    channel_key: str | None = None
    message_template: str | None = None
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


class OutboundWebhookSummary(BaseModel):
    total: int = 0
    active: int = 0
    failing: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
