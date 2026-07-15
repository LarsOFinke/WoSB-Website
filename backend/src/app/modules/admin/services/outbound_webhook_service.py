from __future__ import annotations

import ipaddress
import json
import secrets
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
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
from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES, EVENT_CATALOG, EVENT_TYPES
from app.modules.fleet.models.fleet import Fleet
from app.modules.squads.models.squad import Squad

DISCORD_WEBHOOK_HOSTS = {"discord.com", "ptb.discord.com", "canary.discord.com", "discordapp.com"}


class OutboundWebhookError(ValueError):
    pass


def event_catalog() -> list[OutboundWebhookEventCatalogItem]:
    return [
        OutboundWebhookEventCatalogItem(
            key=key,
            group=group,
            description=description,
            default_template=DEFAULT_MESSAGES.get(
                key, "RBF-Ereignis **{event}** für {resource.type} #{resource.id}."
            ),
        )
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


def _validate_endpoint_url(value: str, delivery_mode: str = "signed_json") -> str:
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise OutboundWebhookError("Webhook endpoint must be a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise OutboundWebhookError("Webhook endpoint URLs must not contain credentials.")
    if parsed.fragment:
        raise OutboundWebhookError("Webhook endpoint URLs must not contain fragments.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise OutboundWebhookError("Webhook endpoint port is invalid.") from exc
    if port is not None and not 1 <= port <= 65535:
        raise OutboundWebhookError("Webhook endpoint port is invalid.")
    if settings.is_production and parsed.scheme != "https":
        raise OutboundWebhookError("Production webhook endpoints must use HTTPS.")

    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise OutboundWebhookError("Webhook endpoints must use a public network host.")
    try:
        literal_address = ipaddress.ip_address(hostname)
    except ValueError:
        literal_address = None
    if literal_address is not None and not literal_address.is_global:
        raise OutboundWebhookError("Webhook endpoints must not target private or reserved addresses.")
    if delivery_mode == "discord":
        if parsed.scheme != "https":
            raise OutboundWebhookError("Discord chat webhooks must use HTTPS.")
        if hostname not in DISCORD_WEBHOOK_HOSTS or not parsed.path.startswith("/api/webhooks/"):
            raise OutboundWebhookError("Discord chat webhooks must use an official Discord webhook URL.")
    return url


def _validate_scope(db: Session, scope_type: str, scope_id: int | None) -> tuple[str, int | None]:
    if scope_type == "global":
        return "global", None
    if scope_id is None:
        raise OutboundWebhookError("A fleet or squad scope requires a scope ID.")
    model = Fleet if scope_type == "fleet" else Squad if scope_type == "squad" else None
    if model is None or db.get(model, scope_id) is None:
        raise OutboundWebhookError(f"Selected {scope_type} scope does not exist.")
    return scope_type, scope_id


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


def _public_endpoint(row: OutboundWebhook) -> str:
    if row.delivery_mode != "discord":
        return row.endpoint_url
    parsed = urlparse(row.endpoint_url)
    parts = [part for part in parsed.path.split("/") if part]
    webhook_id = parts[2] if len(parts) > 2 else "configured"
    return f"{parsed.scheme}://{parsed.netloc}/api/webhooks/{webhook_id}/••••••"


def serialize_webhook(row: OutboundWebhook, *, reveal_secret: bool = False) -> OutboundWebhookRead:
    return OutboundWebhookRead(
        id=row.id,
        name=row.name,
        endpoint_url=_public_endpoint(row),
        event_types=_load_events(row.event_types_json),
        delivery_mode=row.delivery_mode,
        scope_type=row.scope_type,
        scope_id=row.scope_id,
        channel_key=row.channel_key,
        message_template=row.message_template,
        discord_username=row.discord_username,
        discord_avatar_url=row.discord_avatar_url,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by_username=row.created_by_username,
        last_success_at=row.last_success_at,
        last_failure_at=row.last_failure_at,
        secret_hint=_secret_hint(row.signing_secret),
        signing_secret=row.signing_secret if reveal_secret and row.delivery_mode == "signed_json" else None,
    )


def serialize_delivery(row: OutboundWebhookDelivery) -> OutboundWebhookDeliveryRead:
    return OutboundWebhookDeliveryRead(
        id=row.id,
        webhook_id=row.webhook_id,
        webhook_name=row.webhook.name,
        delivery_mode=row.webhook.delivery_mode,
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
    rows = db.scalars(
        select(OutboundWebhook).order_by(OutboundWebhook.name.asc(), OutboundWebhook.id.asc())
    ).all()
    return [serialize_webhook(row) for row in rows]


def webhook_summary(db: Session) -> OutboundWebhookSummary:
    total = int(db.scalar(select(func.count(OutboundWebhook.id))) or 0)
    active = int(
        db.scalar(select(func.count(OutboundWebhook.id)).where(OutboundWebhook.is_active.is_(True))) or 0
    )
    failing = int(
        db.scalar(
            select(func.count(OutboundWebhook.id)).where(
                OutboundWebhook.is_active.is_(True),
                OutboundWebhook.last_failure_at.is_not(None),
                (
                    OutboundWebhook.last_success_at.is_(None)
                    | (OutboundWebhook.last_failure_at > OutboundWebhook.last_success_at)
                ),
            )
        )
        or 0
    )
    by_mode = {
        mode: int(count)
        for mode, count in db.execute(
            select(OutboundWebhook.delivery_mode, func.count(OutboundWebhook.id)).group_by(
                OutboundWebhook.delivery_mode
            )
        ).all()
    }
    successful = int(
        db.scalar(
            select(func.count(OutboundWebhookDelivery.id)).where(
                OutboundWebhookDelivery.status == "success"
            )
        )
        or 0
    )
    failed = int(
        db.scalar(
            select(func.count(OutboundWebhookDelivery.id)).where(
                OutboundWebhookDelivery.status == "failed"
            )
        )
        or 0
    )
    return OutboundWebhookSummary(
        total=total,
        active=active,
        failing=failing,
        discord=by_mode.get("discord", 0),
        signed_json=by_mode.get("signed_json", 0),
        successful_deliveries=successful,
        failed_deliveries=failed,
    )


def _apply_payload(db: Session, row: OutboundWebhook, payload) -> None:
    scope_type, scope_id = _validate_scope(db, payload.scope_type, payload.scope_id)
    row.name = payload.name.strip()
    if payload.endpoint_url is None and row.id is not None and payload.delivery_mode != row.delivery_mode:
        raise OutboundWebhookError("Changing the delivery type requires a new endpoint URL.")
    endpoint_url = payload.endpoint_url or row.endpoint_url
    if not endpoint_url:
        raise OutboundWebhookError("Webhook endpoint URL is required.")
    row.endpoint_url = _validate_endpoint_url(endpoint_url, payload.delivery_mode)
    row.event_types_json = _events_json(payload.event_types)
    row.delivery_mode = payload.delivery_mode
    row.scope_type = scope_type
    row.scope_id = scope_id
    row.channel_key = payload.channel_key if payload.delivery_mode == "signed_json" else None
    row.message_template = payload.message_template
    row.discord_username = payload.discord_username if payload.delivery_mode == "discord" else None
    row.discord_avatar_url = payload.discord_avatar_url if payload.delivery_mode == "discord" else None
    row.is_active = payload.is_active


def create_webhook(db: Session, payload: OutboundWebhookCreate, actor: User) -> OutboundWebhookRead:
    row = OutboundWebhook(
        name=payload.name.strip(),
        endpoint_url=payload.endpoint_url,
        signing_secret=secrets.token_urlsafe(36),
        event_types_json="[]",
        created_by_user_id=actor.id,
        created_by_username=actor.username,
    )
    _apply_payload(db, row, payload)
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
    _apply_payload(db, row, payload)
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return serialize_webhook(row)


def rotate_webhook_secret(db: Session, webhook_id: int) -> OutboundWebhookRead | None:
    row = db.get(OutboundWebhook, webhook_id)
    if row is None:
        return None
    if row.delivery_mode != "signed_json":
        raise OutboundWebhookError("Discord chat webhooks do not use RBF signing secrets.")
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
        query.order_by(
            OutboundWebhookDelivery.created_at.desc(), OutboundWebhookDelivery.id.desc()
        ).limit(limit)
    ).all()
    return [serialize_delivery(row) for row in rows]
