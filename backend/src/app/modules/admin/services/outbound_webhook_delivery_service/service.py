from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

from fastapi import BackgroundTasks
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import OutboundWebhook, OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import OutboundWebhookDeliveryRead
from app.modules.admin.services.outbound_webhook_service import (
    OutboundWebhookError,
    _load_events,
    endpoint_url_for_delivery,
    serialize_delivery,
)
from app.modules.admin.services.webhook_events import EVENT_TYPES

from .discord import discord_payload
from .envelope import WebhookEnvelopeFactory
from .transport import WebhookTransport

logger = logging.getLogger(__name__)

DEFAULT_RECOVERY_STALE_AFTER = timedelta(minutes=5)
DEFAULT_MAX_AUTOMATIC_ATTEMPTS = 3
DEFAULT_RECOVERY_BATCH_SIZE = 100


class WebhookDeliveryService:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
        envelopes: WebhookEnvelopeFactory | None = None,
        transport: WebhookTransport | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._envelopes = envelopes or WebhookEnvelopeFactory()
        self._transport = transport or WebhookTransport()

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
            and self._matches_scope(subscription, event)
        ]
        if not rows:
            return []
        db.add_all(rows)
        db.commit()
        return [row.id for row in rows]

    def queue_event_safely(self, db: Session, **event: Any) -> list[int]:
        try:
            return self.queue_event(db, **event)
        except Exception:  # pragma: no cover - integrations must not break primary actions
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
            attempt_started_at = utc_now()
            claimed = db.execute(
                update(OutboundWebhookDelivery)
                .where(
                    OutboundWebhookDelivery.id == delivery_id,
                    OutboundWebhookDelivery.status == "queued",
                )
                .values(
                    status="processing",
                    attempts=OutboundWebhookDelivery.attempts + 1,
                    last_attempt_at=attempt_started_at,
                    response_status=None,
                    response_body=None,
                    error_message=None,
                )
            ).rowcount
            db.commit()
            if not claimed:
                return

            row = db.get(OutboundWebhookDelivery, delivery_id)
            if row is None:
                return
            webhook = row.webhook
            if not webhook.is_active and row.event_type != "integration.test":
                self._disable(row, webhook)
                db.commit()
                return
            try:
                self._deliver(row, webhook)
            except Exception as exc:  # pragma: no cover - final containment for background tasks
                row.status = "failed"
                row.error_message = f"Unexpected delivery error ({type(exc).__name__})."
                webhook.last_failure_at = utc_now()
                logger.exception(
                    "unexpected outbound webhook delivery failure",
                    extra={
                        "delivery_id": row.delivery_id,
                        "event_type": row.event_type,
                        "webhook_id": webhook.id,
                    },
                )
            db.commit()

    def recover_pending(
        self,
        *,
        stale_after: timedelta = DEFAULT_RECOVERY_STALE_AFTER,
        max_attempts: int = DEFAULT_MAX_AUTOMATIC_ATTEMPTS,
        limit: int = DEFAULT_RECOVERY_BATCH_SIZE,
    ) -> int:
        now = utc_now()
        cutoff = now - max(stale_after, timedelta(0))
        with self._session_factory() as db:
            db.execute(
                update(OutboundWebhookDelivery)
                .where(
                    OutboundWebhookDelivery.status.in_(("queued", "processing")),
                    OutboundWebhookDelivery.attempts >= max_attempts,
                )
                .values(
                    status="failed",
                    error_message="Automatic webhook delivery retry limit reached.",
                )
            )
            candidate_ids = list(
                db.scalars(
                    select(OutboundWebhookDelivery.id)
                    .where(
                        OutboundWebhookDelivery.attempts < max_attempts,
                        or_(
                            and_(
                                OutboundWebhookDelivery.status == "queued",
                                OutboundWebhookDelivery.created_at <= cutoff,
                            ),
                            and_(
                                OutboundWebhookDelivery.status == "processing",
                                or_(
                                    OutboundWebhookDelivery.last_attempt_at.is_(None),
                                    OutboundWebhookDelivery.last_attempt_at <= cutoff,
                                ),
                            ),
                        ),
                    )
                    .order_by(
                        OutboundWebhookDelivery.created_at.asc(),
                        OutboundWebhookDelivery.id.asc(),
                    )
                    .limit(max(1, limit))
                ).all()
            )
            if candidate_ids:
                db.execute(
                    update(OutboundWebhookDelivery)
                    .where(
                        OutboundWebhookDelivery.id.in_(candidate_ids),
                        OutboundWebhookDelivery.status == "processing",
                        or_(
                            OutboundWebhookDelivery.last_attempt_at.is_(None),
                            OutboundWebhookDelivery.last_attempt_at <= cutoff,
                        ),
                    )
                    .values(
                        status="queued",
                        error_message="Recovered after an interrupted delivery attempt.",
                    )
                )
            db.commit()

        for candidate_id in candidate_ids:
            self.attempt(candidate_id)
        return len(candidate_ids)

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
        resource = envelope["resource"]
        row = self._new_row(
            webhook,
            delivery_id=delivery_id,
            event_type=selected_event,
            resource_type=str(resource["type"]),
            resource_id=str(resource["id"]),
            envelope=envelope,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        self.attempt(row.id)
        db.expire_all()
        refreshed = db.get(OutboundWebhookDelivery, row.id)
        return serialize_delivery(refreshed) if refreshed is not None else None

    def create_broadcast(
        self,
        db: Session,
        *,
        webhook_ids: list[int],
        actor: User,
        message: str,
        discord_username: str | None = None,
    ) -> list[OutboundWebhookDeliveryRead]:
        subscriptions = list(
            db.scalars(
                select(OutboundWebhook)
                .where(
                    OutboundWebhook.id.in_(webhook_ids),
                    OutboundWebhook.is_active.is_(True),
                    OutboundWebhook.broadcast_enabled.is_(True),
                )
                .order_by(OutboundWebhook.id.asc())
            ).all()
        )
        if len(subscriptions) != len(set(webhook_ids)):
            raise OutboundWebhookError(
                "Every selected target must be an active broadcast-enabled Discord webhook."
            )
        broadcast_id = f"broadcast-{utc_now().strftime('%Y%m%d%H%M%S%f')}"
        rows: list[OutboundWebhookDelivery] = []
        for webhook in subscriptions:
            delivery_id, envelope = self._envelopes.broadcast(
                webhook,
                actor,
                message=message,
                discord_username=discord_username,
                broadcast_id=broadcast_id,
            )
            rows.append(
                self._new_row(
                    webhook,
                    delivery_id=delivery_id,
                    event_type="broadcast.manual",
                    resource_type="broadcast",
                    resource_id=broadcast_id,
                    envelope=envelope,
                )
            )
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
        return [serialize_delivery(row) for row in rows]

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

    @staticmethod
    def _matches_scope(subscription: OutboundWebhook, event: dict[str, Any]) -> bool:
        if subscription.scope_type == "global":
            return True
        if subscription.scope_type == "fleet":
            return subscription.scope_id == event.get("fleet_id") or (
                event.get("scope_type") == "fleet" and subscription.scope_id == event.get("scope_id")
            )
        if subscription.scope_type == "squad":
            return subscription.scope_id == event.get("squad_id") or (
                event.get("scope_type") == "squad" and subscription.scope_id == event.get("scope_id")
            )
        return False

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
            scope_type=event.get("scope_type", "global"),
            scope_id=event.get("scope_id"),
            fleet_id=event.get("fleet_id"),
            squad_id=event.get("squad_id"),
        )
        return self._new_row(
            subscription,
            delivery_id=delivery_id,
            event_type=event["event_type"],
            resource_type=event["resource_type"],
            resource_id=event["resource_id"],
            envelope=envelope,
        )

    def _deliver(self, row: OutboundWebhookDelivery, webhook: OutboundWebhook) -> None:
        envelope = json.loads(row.payload_json)
        body = json.dumps(
            discord_payload(webhook, envelope), ensure_ascii=False, separators=(",", ":")
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "RoyalBlackwaterFleet-DiscordWebhook/1.0",
        }
        endpoint_url = endpoint_url_for_delivery(webhook)
        request = Request(
            endpoint_url,
            data=body.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            status_code, response_body = self._transport.send(request)
            self._record_response(row, webhook, status_code, response_body)
        except HTTPError as exc:
            row.status = "failed"
            row.response_status = int(exc.code)
            row.response_body = exc.read(4096).decode("utf-8", errors="replace") or None
            row.error_message = f"Endpoint returned HTTP {exc.code}."
            webhook.last_failure_at = utc_now()
        except (URLError, TimeoutError, OSError) as exc:
            row.status = "failed"
            row.error_message = self._transport.error_message(endpoint_url, exc)
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
