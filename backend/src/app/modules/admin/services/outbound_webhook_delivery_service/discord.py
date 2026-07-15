from __future__ import annotations

import json
import re
from typing import Any

from app.modules.admin.models.outbound_webhook import OutboundWebhook
from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES

_TOKEN_PATTERN = re.compile(r"\{\{?\s*([a-zA-Z0-9_.-]+)\s*\}?\}")


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
    template = webhook.message_template or DEFAULT_MESSAGES.get(
        str(envelope.get("event")), "RBF-Ereignis **{event}** für {resource.type} #{resource.id}."
    )
    enriched = {**envelope, "destination": {"name": webhook.name}}
    content = render_message(template, enriched)
    resource_url = _lookup(envelope, "resource.url")
    if resource_url and resource_url not in content:
        content = f"{content}\n{resource_url}".strip()
    payload: dict[str, Any] = {
        "content": (content or f"RBF-Ereignis: {envelope.get('event', 'unknown')}")[:2000],
        "allowed_mentions": {"parse": []},
    }
    if webhook.discord_username:
        payload["username"] = webhook.discord_username
    if webhook.discord_avatar_url:
        payload["avatar_url"] = webhook.discord_avatar_url
    return payload
