from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.core.time import utc_now
from app.modules.accounts.models.user import User
from app.modules.admin.models.outbound_webhook import OutboundWebhook
from app.modules.admin.services.webhook_events import event_test_sample

from .serialization import JsonSafeEncoder


class WebhookEnvelopeFactory:
    SOURCE = "royal-blackwater-fleet"

    def __init__(
        self,
        encoder: JsonSafeEncoder | None = None,
        public_base_url: str | None = None,
    ) -> None:
        self._encoder = encoder or JsonSafeEncoder()
        self._public_base_url = (
            public_base_url.rstrip("/")
            if public_base_url is not None
            else self._default_public_base_url()
        )

    @staticmethod
    def _default_public_base_url() -> str:
        return next(
            (
                origin.rstrip("/")
                for origin in settings.cors_origins
                if origin.startswith(("https://", "http://"))
            ),
            "",
        )

    def _resource_url(self, resource_url: str | None) -> str | None:
        if not resource_url:
            return None
        normalized = resource_url.strip()
        if normalized.startswith(("https://", "http://")):
            return normalized
        if self._public_base_url and normalized.startswith("/"):
            return f"{self._public_base_url}{normalized}"
        return normalized

    def event(
        self,
        subscription: OutboundWebhook,
        *,
        event_type: str,
        resource_type: str,
        resource_id: int | str,
        data: Any,
        actor: User | None,
        resource_url: str | None,
        scope_type: str = "global",
        scope_id: int | None = None,
        fleet_id: int | None = None,
        squad_id: int | None = None,
    ) -> tuple[str, dict[str, Any]]:
        delivery_id = uuid4().hex
        return delivery_id, {
            "id": delivery_id,
            "event": event_type,
            "occurred_at": utc_now().isoformat(),
            "source": self.SOURCE,
            "destination": {
                "message_template": subscription.message_template,
                "scope_type": subscription.scope_type,
                "scope_id": subscription.scope_id,
            },
            "scope": {
                "type": scope_type,
                "id": scope_id,
                "fleet_id": fleet_id,
                "squad_id": squad_id,
            },
            "actor": self._actor(actor),
            "resource": {
                "type": resource_type,
                "id": str(resource_id),
                "url": self._resource_url(resource_url),
            },
            "data": self._encoder.convert(data),
        }

    def test(
        self,
        subscription: OutboundWebhook,
        actor: User,
        event_type: str,
    ) -> tuple[str, dict[str, Any]]:
        sample = event_test_sample(event_type)
        if event_type == "integration.test":
            sample["data"]["webhook_name"] = subscription.name
        return self.event(
            subscription,
            event_type=event_type,
            resource_type=sample["resource_type"],
            resource_id=sample["resource_id"],
            actor=actor,
            resource_url=sample.get("resource_url"),
            scope_type=sample.get("scope_type", "global"),
            scope_id=sample.get("scope_id"),
            fleet_id=sample.get("fleet_id"),
            squad_id=sample.get("squad_id"),
            data=sample["data"],
        )

    def broadcast(
        self,
        subscription: OutboundWebhook,
        actor: User,
        *,
        message: str,
        discord_username: str | None = None,
        discord_avatar_url: str | None = None,
        broadcast_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        delivery_id = uuid4().hex
        resource_id = broadcast_id or uuid4().hex
        return delivery_id, {
            "id": delivery_id,
            "event": "broadcast.manual",
            "occurred_at": utc_now().isoformat(),
            "source": self.SOURCE,
            "destination": {
                "message_template": None,
                "scope_type": subscription.scope_type,
                "scope_id": subscription.scope_id,
            },
            "scope": {
                "type": "global",
                "id": None,
                "fleet_id": None,
                "squad_id": None,
            },
            "actor": self._actor(actor),
            "resource": {
                "type": "broadcast",
                "id": resource_id,
                "url": None,
            },
            "data": {
                "message": message,
                "discord_username": discord_username,
                "discord_avatar_url": discord_avatar_url,
            },
        }

    @staticmethod
    def _actor(actor: User | None) -> dict[str, Any] | None:
        if actor is None:
            return None
        return {
            "id": actor.id,
            "username": actor.username,
            "display_name": actor.display_name,
            "role": actor.role,
        }
