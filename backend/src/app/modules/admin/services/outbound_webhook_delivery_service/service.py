from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import (
    OutboundWebhook,
    OutboundWebhookDelivery,
)
from app.modules.admin.schemas.outbound_webhook import OutboundWebhookDeliveryRead
from app.modules.admin.services.outbound_webhook_service import (
    EVENT_TYPES,
    OutboundWebhookError,
    _load_events,
    serialize_delivery,
)

from .envelope import WebhookEnvelopeFactory
from .transport import WebhookSigner, WebhookTransport

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
        envelopes: WebhookEnvelopeFactory | None = None,
        transport: WebhookTransport | None = None,
        signer: WebhookSigner | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._envelopes = envelopes or WebhookEnvelopeFactory()
        self._transport = transport or WebhookTransport()
        self._signer = signer or WebhookSigner()

    def queue_event(self, db: Session, **event: Any) -> list[int]:
        event_type = event["event_type"]
        if event_type not in EVENT_TYPES:
            raise OutboundWebhookError(f"Unsupported webhook event type: {event_type}")
        subscriptions = db.scalars(
            select(OutboundWebhook)
            .where(OutboundWebhook.is_active.is_(True))
            .order_by(OutboundWebhook.id.asc())
        ).all()
        rows = [
            self._build_event_row(subscription, event)
            for subscription in subscriptions
            if event_type in _load_events(subscription.event_types_json)
        ]
        if not rows:
            return []
        db.add_all(rows)
        db.commit()
        return [row.id for row in rows]

    def queue_event_safely(self, db: Session, **event: Any) -> list[int]:
        try:
            return self.queue_event(db, **event)
        except Exception:  # pragma: no cover - integration must not break primary content
            db.rollback()
            logger.exception(
                "outbound webhook event queue failed",
                extra={
                    "event_type": event.get("event_type"),
                    "resource_id": event.get("resource_id"),
                },
            )
            return []

    @staticmethod
    def schedule(background_tasks: BackgroundTasks, delivery_ids: list[int]) -> None:
        from . import attempt_webhook_delivery

        for delivery_id in delivery_ids:
            background_tasks.add_task(attempt_webhook_delivery, delivery_id)

    def attempt(self, delivery_id: int) -> None:
        with self._session_factory() as db:
            row = db.get(OutboundWebhookDelivery, delivery_id)
            if row is None:
                return
            webhook = row.webhook
            self._begin_attempt(row)
            if not webhook.is_active and row.event_type != "integration.test":
                self._disable(row, webhook)
                db.commit()
                return
            self._deliver(row, webhook)
            db.commit()

    def create_test(
        self,
        db: Session,
        webhook_id: int,
        actor: User,
        event_type: str = "integration.test",
    ) -> OutboundWebhookDeliveryRead | None:
        webhook = db.get(OutboundWebhook, webhook_id)
        if webhook is None:
            return None
        selected_event = event_type if event_type in EVENT_TYPES else "integration.test"
        delivery_id, envelope = self._envelopes.test(webhook, actor, selected_event)
        row = self._new_row(
            webhook,
            delivery_id=delivery_id,
            event_type=selected_event,
            resource_type="integration",
            resource_id=webhook.id,
            envelope=envelope,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        self.attempt(row.id)
        db.expire_all()
        refreshed = db.get(OutboundWebhookDelivery, row.id)
        return serialize_delivery(refreshed) if refreshed is not None else None

    def retry(self, db: Session, delivery_id: int) -> OutboundWebhookDeliveryRead | None:
        row = db.get(OutboundWebhookDelivery, delivery_id)
        if row is None:
            return None
        row.status = "queued"
        row.error_message = None
        db.commit()
        self.attempt(delivery_id)
        db.expire_all()
        refreshed = db.get(OutboundWebhookDelivery, delivery_id)
        return serialize_delivery(refreshed) if refreshed is not None else None

    def _build_event_row(
        self, subscription: OutboundWebhook, event: dict[str, Any]
    ) -> OutboundWebhookDelivery:
        delivery_id, envelope = self._envelopes.event(
            subscription,
            event_type=event["event_type"],
            resource_type=event["resource_type"],
            resource_id=event["resource_id"],
            data=event["data"],
            actor=event.get("actor"),
            resource_url=event.get("resource_url"),
        )
        return self._new_row(
            subscription,
            delivery_id=delivery_id,
            event_type=event["event_type"],
            resource_type=event["resource_type"],
            resource_id=event["resource_id"],
            envelope=envelope,
        )

    def _deliver(
        self, row: OutboundWebhookDelivery, webhook: OutboundWebhook
    ) -> None:
        timestamp = str(int(time.time()))
        request = Request(
            webhook.endpoint_url,
            data=row.payload_json.encode("utf-8"),
            headers=self._signer.headers(row, webhook.signing_secret, timestamp),
            method="POST",
        )
        try:
            status_code, body = self._transport.send(request)
            self._record_response(row, webhook, status_code, body)
        except HTTPError as exc:
            row.status = "failed"
            row.response_status = int(exc.code)
            row.response_body = exc.read(4096).decode("utf-8", errors="replace") or None
            row.error_message = f"Endpoint returned HTTP {exc.code}."
            webhook.last_failure_at = utc_now()
        except (URLError, TimeoutError, OSError) as exc:
            row.status = "failed"
            row.error_message = self._transport.error_message(webhook.endpoint_url, exc)
            webhook.last_failure_at = utc_now()

    @staticmethod
    def _new_row(
        webhook: OutboundWebhook,
        *,
        delivery_id: str,
        event_type: str,
        resource_type: str,
        resource_id: int | str,
        envelope: dict[str, Any],
    ) -> OutboundWebhookDelivery:
        return OutboundWebhookDelivery(
            webhook_id=webhook.id,
            delivery_id=delivery_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=str(resource_id),
            payload_json=json.dumps(envelope, ensure_ascii=False, separators=(",", ":")),
            status="queued",
        )

    @staticmethod
    def _begin_attempt(row: OutboundWebhookDelivery) -> None:
        row.attempts += 1
        row.last_attempt_at = utc_now()
        row.response_status = None
        row.response_body = None
        row.error_message = None

    @staticmethod
    def _disable(row: OutboundWebhookDelivery, webhook: OutboundWebhook) -> None:
        row.status = "failed"
        row.error_message = "Webhook subscription is disabled."
        webhook.last_failure_at = row.last_attempt_at

    @staticmethod
    def _record_response(
        row: OutboundWebhookDelivery,
        webhook: OutboundWebhook,
        status_code: int,
        response_body: str,
    ) -> None:
        row.response_status = status_code
        row.response_body = response_body or None
        if 200 <= status_code < 300:
            row.status = "success"
            row.delivered_at = utc_now()
            webhook.last_success_at = row.delivered_at
        else:
            row.status = "failed"
            row.error_message = f"Endpoint returned HTTP {status_code}."
            webhook.last_failure_at = utc_now()
