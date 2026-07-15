from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import OutboundWebhookDeliveryRead

from .envelope import WebhookEnvelopeFactory
from .serialization import JsonSafeEncoder
from .service import WebhookDeliveryService
from .transport import WebhookSigner, WebhookTransport

_default_service = WebhookDeliveryService()


def _json_safe(value: Any) -> Any:
    return JsonSafeEncoder().convert(value)


def _delivery_headers(
    row: OutboundWebhookDelivery, secret: str, timestamp: str
) -> dict[str, str]:
    return WebhookSigner.headers(row, secret, timestamp)


def _delivery_transport_error(endpoint_url: str, exc: Exception) -> str:
    return WebhookTransport.error_message(endpoint_url, exc)


def queue_webhook_event(db: Session, **event: Any) -> list[int]:
    return _default_service.queue_event(db, **event)


def queue_webhook_event_safely(db: Session, **event: Any) -> list[int]:
    return _default_service.queue_event_safely(db, **event)


def schedule_webhook_deliveries(
    background_tasks: BackgroundTasks, delivery_ids: list[int]
) -> None:
    _default_service.schedule(background_tasks, delivery_ids)


def attempt_webhook_delivery(delivery_id: int) -> None:
    _default_service.attempt(delivery_id)


def create_test_delivery(
    db: Session,
    webhook_id: int,
    actor: User,
    event_type: str = "integration.test",
) -> OutboundWebhookDeliveryRead | None:
    return _default_service.create_test(db, webhook_id, actor, event_type)


def retry_delivery(
    db: Session, delivery_id: int
) -> OutboundWebhookDeliveryRead | None:
    return _default_service.retry(db, delivery_id)


__all__ = [
    "JsonSafeEncoder",
    "WebhookDeliveryService",
    "WebhookEnvelopeFactory",
    "WebhookSigner",
    "WebhookTransport",
    "attempt_webhook_delivery",
    "create_test_delivery",
    "queue_webhook_event",
    "queue_webhook_event_safely",
    "retry_delivery",
    "schedule_webhook_deliveries",
]
