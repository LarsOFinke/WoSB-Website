from __future__ import annotations

import ipaddress
import json
import re
from urllib.parse import urlparse

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.secret_box import SecretBoxError, webhook_secret_box
from app.core.time import utc_now
from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import OutboundWebhook, OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import (
    OutboundWebhookCreate,
    OutboundWebhookDeliveryDeleteResult,
    OutboundWebhookDeliveryRead,
    OutboundWebhookEventCatalogItem,
    OutboundWebhookRead,
    OutboundWebhookSummary,
    OutboundWebhookUpdate,
)
from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES, EVENT_CATALOG, EVENT_TYPES
from app.modules.fleet.models.fleet import Fleet
from app.modules.squads.models.squad import Squad

DISCORD_WEBHOOK_HOSTS = {
    "discord.com",
    "www.discord.com",
    "ptb.discord.com",
    "canary.discord.com",
    "discordapp.com",
}
DISCORD_WEBHOOK_PATH = re.compile(
    r"^/api(?:/v\d{1,2})?/webhooks/(?P<webhook_id>[^/\s]+)/(?P<token>[^/\s]+)(?:/(?:github|slack))?/?$",
    re.IGNORECASE,
)


class OutboundWebhookError(ValueError):
    pass


def event_catalog() -> list[OutboundWebhookEventCatalogItem]:
    return [
        OutboundWebhookEventCatalogItem(
            key=key,
            group=group,
            description=description,
            default_template=DEFAULT_MESSAGES.get(
                key, "RBF event **{event}** for {resource.type} #{resource.id}."
            ),
        )
        for key, group, description in EVENT_CATALOG
    ]


def _normalize_event_types(values: list[str], *, allow_empty: bool = False) -> list[str]:
    events = sorted({str(value).strip() for value in values if str(value).strip()})
    unknown = [event for event in events if event not in EVENT_TYPES]
    if unknown:
        raise OutboundWebhookError(f"Unsupported webhook event type: {', '.join(unknown)}")
    if not events and not allow_empty:
        raise OutboundWebhookError("Select at least one webhook event type.")
    return events


def _validate_endpoint_url(value: str) -> str:
    url = value.strip()
    # Discord and Markdown clients sometimes copy a link wrapped in angle brackets.
    if len(url) > 2 and url.startswith("<") and url.endswith(">"):
        url = url[1:-1].strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or not parsed.hostname:
        raise OutboundWebhookError("Discord chat webhooks must use a valid HTTPS URL.")
    if parsed.username or parsed.password:
        raise OutboundWebhookError("Discord webhook URLs must not contain URL credentials.")
    if parsed.fragment:
        raise OutboundWebhookError("Discord webhook URLs must not contain fragments.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise OutboundWebhookError("Discord webhook port is invalid.") from exc
    if port is not None and not 1 <= port <= 65535:
        raise OutboundWebhookError("Discord webhook port is invalid.")

    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise OutboundWebhookError("Discord webhooks must use a public network host.")
    try:
        literal_address = ipaddress.ip_address(hostname)
    except ValueError:
        literal_address = None
    if literal_address is not None and not literal_address.is_global:
        raise OutboundWebhookError("Discord webhooks must not target private or reserved addresses.")
    if hostname not in DISCORD_WEBHOOK_HOSTS:
        raise OutboundWebhookError("Use an official Discord channel webhook URL from discord.com.")
    if not DISCORD_WEBHOOK_PATH.fullmatch(parsed.path):
        raise OutboundWebhookError(
            "The Discord webhook URL must contain both the webhook ID and token. "
            "Copy it from Discord channel settings under Integrations > Webhooks."
        )
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


def _events_json(values: list[str], *, allow_empty: bool = False) -> str:
    return json.dumps(
        _normalize_event_types(values, allow_empty=allow_empty),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _load_events(value: str) -> list[str]:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in payload] if isinstance(payload, list) else []


def endpoint_url_for_delivery(row: OutboundWebhook) -> str:
    try:
        endpoint_url = webhook_secret_box.decrypt(row.endpoint_url)
    except SecretBoxError as exc:
        raise OutboundWebhookError(
            "Stored Discord webhook credential cannot be decrypted. Re-enter the webhook URL."
        ) from exc
    # Treat persisted data as untrusted as well: encryption protects secrecy and
    # integrity, while this allowlist check preserves the outbound SSRF boundary.
    return _validate_endpoint_url(endpoint_url)


def _public_endpoint(row: OutboundWebhook) -> str:
    parsed = urlparse(endpoint_url_for_delivery(row))
    path_match = DISCORD_WEBHOOK_PATH.fullmatch(parsed.path)
    webhook_id = path_match.group("webhook_id") if path_match else "configured"
    return f"{parsed.scheme}://{parsed.netloc}/api/webhooks/{webhook_id}/••••••"


def serialize_webhook(row: OutboundWebhook) -> OutboundWebhookRead:
    return OutboundWebhookRead(
        id=row.id,
        name=row.name,
        endpoint_url=_public_endpoint(row),
        event_types=_load_events(row.event_types_json),
        scope_type=row.scope_type,
        scope_id=row.scope_id,
        message_template=row.message_template,
        discord_username=row.discord_username,
        broadcast_enabled=row.broadcast_enabled,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by_username=row.created_by_username,
        last_success_at=row.last_success_at,
        last_failure_at=row.last_failure_at,
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


def list_webhooks(db: Session, purpose: str | None = None) -> list[OutboundWebhookRead]:
    rows = db.scalars(
        select(OutboundWebhook).order_by(OutboundWebhook.name.asc(), OutboundWebhook.id.asc())
    ).all()
    if purpose == "automation":
        rows = [row for row in rows if _load_events(row.event_types_json)]
    elif purpose == "broadcast":
        rows = [row for row in rows if row.broadcast_enabled]
    return [serialize_webhook(row) for row in rows]


def list_broadcast_webhooks(db: Session) -> list[OutboundWebhookRead]:
    rows = db.scalars(
        select(OutboundWebhook)
        .where(
            OutboundWebhook.is_active.is_(True),
            OutboundWebhook.broadcast_enabled.is_(True),
        )
        .order_by(OutboundWebhook.name.asc(), OutboundWebhook.id.asc())
    ).all()
    return [serialize_webhook(row) for row in rows]


def webhook_summary(db: Session, purpose: str | None = None) -> OutboundWebhookSummary:
    rows = db.scalars(select(OutboundWebhook)).all()
    if purpose == "automation":
        rows = [row for row in rows if _load_events(row.event_types_json)]
    elif purpose == "broadcast":
        rows = [row for row in rows if row.broadcast_enabled]
    webhook_ids = [row.id for row in rows]
    total = len(rows)
    active = sum(1 for row in rows if row.is_active)
    failing = sum(
        1
        for row in rows
        if row.is_active
        and row.last_failure_at is not None
        and (row.last_success_at is None or row.last_failure_at > row.last_success_at)
    )
    successful = 0
    failed = 0
    if webhook_ids:
        successful = int(
            db.scalar(
                select(func.count(OutboundWebhookDelivery.id)).where(
                    OutboundWebhookDelivery.webhook_id.in_(webhook_ids),
                    OutboundWebhookDelivery.status == "success",
                )
            )
            or 0
        )
        failed = int(
            db.scalar(
                select(func.count(OutboundWebhookDelivery.id)).where(
                    OutboundWebhookDelivery.webhook_id.in_(webhook_ids),
                    OutboundWebhookDelivery.status == "failed",
                )
            )
            or 0
        )
    return OutboundWebhookSummary(
        total=total,
        active=active,
        failing=failing,
        successful_deliveries=successful,
        failed_deliveries=failed,
    )


def _apply_payload(db: Session, row: OutboundWebhook, payload: OutboundWebhookCreate | OutboundWebhookUpdate) -> None:
    scope_type, scope_id = _validate_scope(db, payload.scope_type, payload.scope_id)
    row.name = payload.name.strip()
    if payload.endpoint_url:
        endpoint_url = _validate_endpoint_url(payload.endpoint_url)
        row.endpoint_url = webhook_secret_box.encrypt(endpoint_url)
    elif not row.endpoint_url:
        raise OutboundWebhookError("Discord webhook URL is required.")
    row.event_types_json = _events_json(
        payload.event_types, allow_empty=payload.broadcast_enabled
    )
    row.scope_type = scope_type
    row.scope_id = scope_id
    row.message_template = payload.message_template
    row.discord_username = payload.discord_username
    row.broadcast_enabled = payload.broadcast_enabled
    row.is_active = payload.is_active


def encrypt_legacy_webhook_endpoints(db: Session, *, commit: bool = True) -> int:
    """Encrypt plaintext endpoints and rotate ciphertext to the active key."""
    rows = db.scalars(select(OutboundWebhook)).all()
    changed = 0
    for row in rows:
        if not row.endpoint_url:
            continue
        try:
            if webhook_secret_box.is_encrypted(row.endpoint_url):
                replacement = webhook_secret_box.rotate(row.endpoint_url)
            else:
                replacement = webhook_secret_box.encrypt(
                    _validate_endpoint_url(row.endpoint_url)
                )
        except SecretBoxError as exc:
            raise OutboundWebhookError(
                f"Webhook {row.id} credential cannot be decrypted; re-enter its URL."
            ) from exc
        if replacement != row.endpoint_url:
            row.endpoint_url = replacement
            changed += 1
    if changed and commit:
        db.commit()
    return changed


def create_webhook(db: Session, payload: OutboundWebhookCreate, actor: User) -> OutboundWebhookRead:
    row = OutboundWebhook(
        name=payload.name.strip(),
        endpoint_url=payload.endpoint_url,
        event_types_json="[]",
        created_by_user_id=actor.id,
        created_by_username=actor.username,
    )
    _apply_payload(db, row, payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_webhook(row)


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
    event_type: str | None = None,
    limit: int = 100,
) -> list[OutboundWebhookDeliveryRead]:
    query = select(OutboundWebhookDelivery)
    if webhook_id is not None:
        query = query.where(OutboundWebhookDelivery.webhook_id == webhook_id)
    if status:
        query = query.where(OutboundWebhookDelivery.status == status)
    if event_type:
        query = query.where(OutboundWebhookDelivery.event_type == event_type)
    rows = db.scalars(
        query.order_by(
            OutboundWebhookDelivery.created_at.desc(), OutboundWebhookDelivery.id.desc()
        ).limit(limit)
    ).all()
    return [serialize_delivery(row) for row in rows]


def delete_delivery(db: Session, delivery_id: int) -> OutboundWebhookDeliveryDeleteResult:
    row = db.get(OutboundWebhookDelivery, delivery_id)
    if row is None:
        return OutboundWebhookDeliveryDeleteResult(deleted_count=0)
    db.delete(row)
    db.commit()
    return OutboundWebhookDeliveryDeleteResult(deleted_count=1)


def delete_deliveries(
    db: Session,
    *,
    webhook_id: int | None = None,
    status: str | None = None,
    event_type: str | None = None,
) -> OutboundWebhookDeliveryDeleteResult:
    conditions = []
    if webhook_id is not None:
        conditions.append(OutboundWebhookDelivery.webhook_id == webhook_id)
    if status:
        conditions.append(OutboundWebhookDelivery.status == status)
    if event_type:
        conditions.append(OutboundWebhookDelivery.event_type == event_type)
    statement = delete(OutboundWebhookDelivery)
    if conditions:
        statement = statement.where(*conditions)
    result = db.execute(statement)
    db.commit()
    return OutboundWebhookDeliveryDeleteResult(deleted_count=max(int(result.rowcount or 0), 0))
