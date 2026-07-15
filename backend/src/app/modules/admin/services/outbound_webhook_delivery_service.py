from __future__ import annotations

import hashlib
import hmac
import json
import logging
import socket
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import OutboundWebhook, OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import OutboundWebhookDeliveryRead
from app.modules.admin.services.outbound_webhook_service import (
    EVENT_TYPES,
    OutboundWebhookError,
    _load_events,
    serialize_delivery,
)


logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value

def queue_webhook_event(
    db: Session,
    *,
    event_type: str,
    resource_type: str,
    resource_id: int | str,
    data: Any,
    actor: User | None = None,
    resource_url: str | None = None,
) -> list[int]:
    if event_type not in EVENT_TYPES:
        raise OutboundWebhookError(f"Unsupported webhook event type: {event_type}")
    subscriptions = db.scalars(
        select(OutboundWebhook).where(OutboundWebhook.is_active.is_(True)).order_by(OutboundWebhook.id.asc())
    ).all()
    delivery_rows: list[OutboundWebhookDelivery] = []
    occurred_at = utc_now().isoformat()
    for subscription in subscriptions:
        if event_type not in _load_events(subscription.event_types_json):
            continue
        delivery_uuid = uuid4().hex
        envelope = {
            "id": delivery_uuid,
            "event": event_type,
            "occurred_at": occurred_at,
            "source": "royal-blackwater-fleet",
            "destination": {
                "channel_key": subscription.channel_key,
                "message_template": subscription.message_template,
            },
            "actor": (
                {
                    "id": actor.id,
                    "username": actor.username,
                    "display_name": actor.display_name,
                    "role": actor.role,
                }
                if actor is not None
                else None
            ),
            "resource": {
                "type": resource_type,
                "id": str(resource_id),
                "url": resource_url,
            },
            "data": _json_safe(data),
        }
        row = OutboundWebhookDelivery(
            webhook_id=subscription.id,
            delivery_id=delivery_uuid,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=str(resource_id),
            payload_json=json.dumps(envelope, ensure_ascii=False, separators=(",", ":")),
            status="queued",
        )
        db.add(row)
        delivery_rows.append(row)
    if not delivery_rows:
        return []
    db.commit()
    return [row.id for row in delivery_rows]

def queue_webhook_event_safely(db: Session, **kwargs: Any) -> list[int]:
    try:
        return queue_webhook_event(db, **kwargs)
    except Exception:  # pragma: no cover - outbound integration must never roll back primary content
        db.rollback()
        logger.exception(
            "outbound webhook event queue failed",
            extra={"event_type": kwargs.get("event_type"), "resource_id": kwargs.get("resource_id")},
        )
        return []

def schedule_webhook_deliveries(background_tasks: BackgroundTasks, delivery_ids: list[int]) -> None:
    for delivery_id in delivery_ids:
        background_tasks.add_task(attempt_webhook_delivery, delivery_id)

def _delivery_headers(row: OutboundWebhookDelivery, secret: str, timestamp: str) -> dict[str, str]:
    body = row.payload_json.encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "RoyalBlackwaterFleet-Webhook/1.0",
        "X-RBF-Event": row.event_type,
        "X-RBF-Delivery": row.delivery_id,
        "X-RBF-Timestamp": timestamp,
        "X-RBF-Signature": f"sha256={signature}",
    }

def _delivery_transport_error(endpoint_url: str, exc: Exception) -> str:
    host = urlparse(endpoint_url).hostname or "configured endpoint"
    reason = exc.reason if isinstance(exc, URLError) else exc
    if isinstance(reason, socket.gaierror):
        return (
            f"DNS resolution failed for webhook host '{host}'. "
            "Verify the API container outbound network and DNS configuration."
        )
    if isinstance(exc, TimeoutError):
        return f"Connection to webhook host '{host}' timed out."
    return str(exc)[:2000]

def attempt_webhook_delivery(delivery_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.get(OutboundWebhookDelivery, delivery_id)
        if row is None:
            return
        webhook = row.webhook
        row.attempts += 1
        row.last_attempt_at = utc_now()
        row.response_status = None
        row.response_body = None
        row.error_message = None
        if not webhook.is_active and row.event_type != "integration.test":
            row.status = "failed"
            row.error_message = "Webhook subscription is disabled."
            webhook.last_failure_at = row.last_attempt_at
            db.commit()
            return

        timestamp = str(int(time.time()))
        request = Request(
            webhook.endpoint_url,
            data=row.payload_json.encode("utf-8"),
            headers=_delivery_headers(row, webhook.signing_secret, timestamp),
            method="POST",
        )
        try:
            with urlopen(request, timeout=8) as response:  # noqa: S310 - admin-configured integration URL
                response_body = response.read(4096).decode("utf-8", errors="replace")
                row.response_status = int(response.status)
                row.response_body = response_body or None
                if 200 <= int(response.status) < 300:
                    row.status = "success"
                    row.delivered_at = utc_now()
                    webhook.last_success_at = row.delivered_at
                else:
                    row.status = "failed"
                    row.error_message = f"Endpoint returned HTTP {response.status}."
                    webhook.last_failure_at = utc_now()
        except HTTPError as exc:
            row.status = "failed"
            row.response_status = int(exc.code)
            row.response_body = exc.read(4096).decode("utf-8", errors="replace") or None
            row.error_message = f"Endpoint returned HTTP {exc.code}."
            webhook.last_failure_at = utc_now()
        except (URLError, TimeoutError, OSError) as exc:
            row.status = "failed"
            row.error_message = _delivery_transport_error(webhook.endpoint_url, exc)
            webhook.last_failure_at = utc_now()
        db.commit()
    finally:
        db.close()

def create_test_delivery(
    db: Session,
    webhook_id: int,
    actor: User,
    event_type: str = "integration.test",
) -> OutboundWebhookDeliveryRead | None:
    webhook = db.get(OutboundWebhook, webhook_id)
    if webhook is None:
        return None
    selected_event = event_type if event_type in EVENT_TYPES else "integration.test"
    delivery_uuid = uuid4().hex
    envelope = {
        "id": delivery_uuid,
        "event": selected_event,
        "occurred_at": utc_now().isoformat(),
        "source": "royal-blackwater-fleet",
        "destination": {
            "channel_key": webhook.channel_key,
            "message_template": webhook.message_template,
        },
        "actor": {
            "id": actor.id,
            "username": actor.username,
            "display_name": actor.display_name,
            "role": actor.role,
        },
        "resource": {"type": "integration", "id": str(webhook.id), "url": None},
        "data": {
            "message": "Royal Blackwater Fleet webhook test delivery.",
            "webhook_name": webhook.name,
        },
    }
    row = OutboundWebhookDelivery(
        webhook_id=webhook.id,
        delivery_id=delivery_uuid,
        event_type=selected_event,
        resource_type="integration",
        resource_id=str(webhook.id),
        payload_json=json.dumps(envelope, ensure_ascii=False, separators=(",", ":")),
        status="queued",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    attempt_webhook_delivery(row.id)
    db.expire_all()
    refreshed = db.get(OutboundWebhookDelivery, row.id)
    return serialize_delivery(refreshed) if refreshed is not None else None

def retry_delivery(db: Session, delivery_id: int) -> OutboundWebhookDeliveryRead | None:
    row = db.get(OutboundWebhookDelivery, delivery_id)
    if row is None:
        return None
    row.status = "queued"
    row.error_message = None
    db.commit()
    attempt_webhook_delivery(delivery_id)
    db.expire_all()
    refreshed = db.get(OutboundWebhookDelivery, delivery_id)
    return serialize_delivery(refreshed) if refreshed is not None else None
