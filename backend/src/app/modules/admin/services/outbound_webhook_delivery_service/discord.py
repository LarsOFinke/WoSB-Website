from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import settings
from app.modules.admin.models.outbound_webhook import OutboundWebhook
from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES

_TOKEN_PATTERN = re.compile(r"\{\{?\s*([a-zA-Z0-9_.-]+)\s*\}?\}")
FLEET_AVATAR_PATH = "/rbf-fleet-icon.png"


def fleet_avatar_url() -> str:
    public_origin = next(
        (
            origin.rstrip("/")
            for origin in settings.cors_origins
            if origin.startswith(("https://", "http://"))
        ),
        "",
    )
    return f"{public_origin}{FLEET_AVATAR_PATH}" if public_origin else FLEET_AVATAR_PATH


def _lookup(payload: dict[str, Any], path: str) -> str:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return ""
        current = current[part]
    if current is None:
        return ""
    if isinstance(current, (dict, list)):
        return json.dumps(current, ensure_ascii=False, separators=(",", ":"))
    return str(current)


def render_message(template: str, envelope: dict[str, Any]) -> str:
    return _TOKEN_PATTERN.sub(lambda match: _lookup(envelope, match.group(1)), template).strip()


def discord_payload(webhook: OutboundWebhook, envelope: dict[str, Any]) -> dict[str, Any]:
    event_type = str(envelope.get("event"))
    data = envelope.get("data") if isinstance(envelope.get("data"), dict) else {}
    if event_type == "broadcast.manual":
        content = str(data.get("message") or "").strip()
        username = str(data.get("discord_username") or "").strip() or webhook.discord_username
    else:
        template = webhook.message_template or DEFAULT_MESSAGES.get(
            event_type, "RBF event **{event}** for {resource.type} #{resource.id}."
        )
        enriched = {**envelope, "destination": {"name": webhook.name}}
        content = render_message(template, enriched)
        resource_url = _lookup(envelope, "resource.url")
        if resource_url and resource_url not in content:
            content = f"{content}\n{resource_url}".strip()
        username = webhook.discord_username
    payload: dict[str, Any] = {
        "content": (content or f"RBF event: {event_type or 'unknown'}")[:2000],
        "allowed_mentions": {"parse": []},
        "avatar_url": fleet_avatar_url(),
    }
    if username:
        payload["username"] = username
    return payload
