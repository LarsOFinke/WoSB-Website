from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import OutboundWebhook, OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import (
    OutboundWebhookCreate,
    OutboundWebhookDeliveryRead,
    OutboundWebhookEventCatalogItem,
    OutboundWebhookRead,
    OutboundWebhookSummary,
    OutboundWebhookUpdate,
)


logger = logging.getLogger(__name__)


EVENT_CATALOG = (
    ("integration.test", "integration", "Manual connectivity and signature test."),
    ("calendar.event.created", "calendar", "A fleet or squad event was created."),
    ("calendar.event.updated", "calendar", "A fleet or squad event was updated."),
    ("calendar.event.cancelled", "calendar", "A fleet or squad event was cancelled."),
    ("guide.created", "content", "A new guide was published."),
    ("guide.updated", "content", "A published guide was updated."),
    ("guide.removed", "content", "A guide was removed from publication."),
    ("newcomer_guide.updated", "content", "The starter guide was updated."),
    ("build.created", "builds", "A new build was created."),
    ("build.updated", "builds", "A build was updated."),
    ("build.removed", "builds", "A build was removed."),
    ("forum.thread.created", "forum", "A new forum thread was created."),
    ("forum.thread.updated", "forum", "A forum thread was updated."),
)
EVENT_TYPES = {row[0] for row in EVENT_CATALOG}


class OutboundWebhookError(ValueError):
    pass


def event_catalog() -> list[OutboundWebhookEventCatalogItem]:
    return [
        OutboundWebhookEventCatalogItem(key=key, group=group, description=description)
        for key, group, description in EVENT_CATALOG
    ]


def _normalize_event_types(values: list[str]) -> list[str]:
    events = sorted({str(value).strip() for value in values if str(value).strip()})
    unknown = [event for event in events if event not in EVENT_TYPES]
    if unknown:
        raise OutboundWebhookError(f"Unsupported webhook event type: {', '.join(unknown)}")
    if not events:
        raise OutboundWebhookError("Select at least one webhook event type.")
    return events


def _validate_endpoint_url(value: str) -> str:
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise OutboundWebhookError("Webhook endpoint must be a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise OutboundWebhookError("Webhook endpoint URLs must not contain credentials.")
    if settings.is_production and parsed.scheme != "https":
        raise OutboundWebhookError("Production webhook endpoints must use HTTPS.")
    return url


def _events_json(values: list[str]) -> str:
    return json.dumps(_normalize_event_types(values), ensure_ascii=False, separators=(",", ":"))


def _load_events(value: str) -> list[str]:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in payload] if isinstance(payload, list) else []


def _secret_hint(secret: str) -> str:
    return f"••••••{secret[-6:]}" if secret else "••••••"


def serialize_webhook(row: OutboundWebhook, *, reveal_secret: bool = False) -> OutboundWebhookRead:
    return OutboundWebhookRead(
        id=row.id,
        name=row.name,
        endpoint_url=row.endpoint_url,
        event_types=_load_events(row.event_types_json),
        channel_key=row.channel_key,
        message_template=row.message_template,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by_username=row.created_by_username,
        last_success_at=row.last_success_at,
        last_failure_at=row.last_failure_at,
        secret_hint=_secret_hint(row.signing_secret),
        signing_secret=row.signing_secret if reveal_secret else None,
    )


def serialize_delivery(row: OutboundWebhookDelivery) -> OutboundWebhookDeliveryRead:
    return OutboundWebhookDeliveryRead(
        id=row.id,
        webhook_id=row.webhook_id,
        webhook_name=row.webhook.name,
        delivery_id=row.delivery_id,
        event_type=row.event_type,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        status=row.status,
        attempts=row.attempts,
        response_status=row.response_status,
        response_body=row.response_body,
        error_message=row.error_message,
        created_at=row.created_at,
        last_attempt_at=row.last_attempt_at,
        delivered_at=row.delivered_at,
    )


def list_webhooks(db: Session) -> list[OutboundWebhookRead]:
    rows = db.scalars(select(OutboundWebhook).order_by(OutboundWebhook.name.asc(), OutboundWebhook.id.asc())).all()
    return [serialize_webhook(row) for row in rows]


def webhook_summary(db: Session) -> OutboundWebhookSummary:
    total = int(db.scalar(select(func.count(OutboundWebhook.id))) or 0)
    active = int(db.scalar(select(func.count(OutboundWebhook.id)).where(OutboundWebhook.is_active.is_(True))) or 0)
    failing = int(
        db.scalar(
            select(func.count(OutboundWebhook.id)).where(
                OutboundWebhook.is_active.is_(True),
                OutboundWebhook.last_failure_at.is_not(None),
                (OutboundWebhook.last_success_at.is_(None) | (OutboundWebhook.last_failure_at > OutboundWebhook.last_success_at)),
            )
        )
        or 0
    )
    successful = int(
        db.scalar(select(func.count(OutboundWebhookDelivery.id)).where(OutboundWebhookDelivery.status == "success"))
        or 0
    )
    failed = int(
        db.scalar(select(func.count(OutboundWebhookDelivery.id)).where(OutboundWebhookDelivery.status == "failed"))
        or 0
    )
    return OutboundWebhookSummary(
        total=total,
        active=active,
        failing=failing,
        successful_deliveries=successful,
        failed_deliveries=failed,
    )


def create_webhook(db: Session, payload: OutboundWebhookCreate, actor: User) -> OutboundWebhookRead:
    secret = secrets.token_urlsafe(36)
    row = OutboundWebhook(
        name=payload.name.strip(),
        endpoint_url=_validate_endpoint_url(payload.endpoint_url),
        signing_secret=secret,
        event_types_json=_events_json(payload.event_types),
        channel_key=payload.channel_key,
        message_template=payload.message_template,
        is_active=payload.is_active,
        created_by_user_id=actor.id,
        created_by_username=actor.username,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_webhook(row, reveal_secret=True)


def update_webhook(
    db: Session, webhook_id: int, payload: OutboundWebhookUpdate
) -> OutboundWebhookRead | None:
    row = db.get(OutboundWebhook, webhook_id)
    if row is None:
        return None
    row.name = payload.name.strip()
    row.endpoint_url = _validate_endpoint_url(payload.endpoint_url)
    row.event_types_json = _events_json(payload.event_types)
    row.channel_key = payload.channel_key
    row.message_template = payload.message_template
    row.is_active = payload.is_active
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return serialize_webhook(row)


def rotate_webhook_secret(db: Session, webhook_id: int) -> OutboundWebhookRead | None:
    row = db.get(OutboundWebhook, webhook_id)
    if row is None:
        return None
    row.signing_secret = secrets.token_urlsafe(36)
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return serialize_webhook(row, reveal_secret=True)


def delete_webhook(db: Session, webhook_id: int) -> bool:
    row = db.get(OutboundWebhook, webhook_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def list_deliveries(
    db: Session,
    *,
    webhook_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[OutboundWebhookDeliveryRead]:
    query = select(OutboundWebhookDelivery)
    if webhook_id is not None:
        query = query.where(OutboundWebhookDelivery.webhook_id == webhook_id)
    if status:
        query = query.where(OutboundWebhookDelivery.status == status)
    rows = db.scalars(
        query.order_by(OutboundWebhookDelivery.created_at.desc(), OutboundWebhookDelivery.id.desc()).limit(limit)
    ).all()
    return [serialize_delivery(row) for row in rows]


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
            row.error_message = str(exc)[:2000]
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
