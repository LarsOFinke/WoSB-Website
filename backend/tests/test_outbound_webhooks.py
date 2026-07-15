import json
import socket
from urllib.error import URLError

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import OutboundWebhookCreate
from app.modules.admin.services.outbound_webhook_delivery_service import (
    _delivery_transport_error,
    queue_webhook_event,
)
from app.modules.admin.services.outbound_webhook_service import create_webhook
from app.modules.registry import register_all_models
from main import app


def isolated_session() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_webhook_service_queues_matching_signed_delivery_payload() -> None:
    with isolated_session() as db:
        actor = create_user(
            db,
            username="webhook-service-admin",
            password="BlackwaterWebhookService123!",
            display_name="Webhook Service Admin",
            role=ROLE_ADMIN,
        )
        created = create_webhook(
            db,
            OutboundWebhookCreate(
                name="Discord events",
                endpoint_url="http://bot.example.test/hooks/events",
                event_types=["calendar.event.created", "guide.created"],
                channel_key="events",
                message_template="New event: {data.title}",
            ),
            actor,
        )
        assert created.signing_secret
        assert created.secret_hint.endswith(created.signing_secret[-6:])

        delivery_ids = queue_webhook_event(
            db,
            event_type="calendar.event.created",
            resource_type="calendar_event",
            resource_id=42,
            resource_url="/calendar/events/42",
            actor=actor,
            data={"id": 42, "title": "Port battle"},
        )
        assert len(delivery_ids) == 1
        delivery = db.scalar(select(OutboundWebhookDelivery).where(OutboundWebhookDelivery.id == delivery_ids[0]))
        payload = json.loads(delivery.payload_json)
        assert payload["event"] == "calendar.event.created"
        assert payload["destination"]["channel_key"] == "events"
        assert payload["resource"]["url"] == "/calendar/events/42"
        assert payload["data"]["title"] == "Port battle"

        ignored = queue_webhook_event(
            db,
            event_type="build.created",
            resource_type="build",
            resource_id=7,
            actor=actor,
            data={"id": 7},
        )
        assert ignored == []


def test_admin_can_manage_webhooks_and_secret_is_only_revealed_on_create_or_rotate() -> None:
    username = "webhook-route-admin"
    password = "BlackwaterWebhookRoute123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Webhook Route Admin",
                role=ROLE_ADMIN,
            )
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200

        created = client.post(
            "/api/admin/integrations/webhooks",
            json={
                "name": "Discord guides",
                "endpoint_url": "http://bot.example.test/hooks/guides",
                "event_types": ["guide.created", "guide.updated"],
                "channel_key": "guides",
                "message_template": "{data.title}",
                "is_active": True,
            },
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["signing_secret"]
        webhook_id = body["id"]

        listing = client.get("/api/admin/integrations/webhooks")
        assert listing.status_code == 200
        listed = next(row for row in listing.json() if row["id"] == webhook_id)
        assert listed["signing_secret"] is None
        assert listed["event_types"] == ["guide.created", "guide.updated"]

        rotated = client.post(f"/api/admin/integrations/webhooks/{webhook_id}/rotate-secret", json={})
        assert rotated.status_code == 200
        assert rotated.json()["signing_secret"]
        assert rotated.json()["signing_secret"] != body["signing_secret"]

        deleted = client.delete(f"/api/admin/integrations/webhooks/{webhook_id}")
        assert deleted.status_code == 204


def test_moderator_cannot_view_or_manage_outbound_webhooks() -> None:
    username = "webhook-readonly-moderator"
    password = "BlackwaterWebhookReadonly123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Webhook Readonly Moderator",
                role=ROLE_MODERATOR,
            )
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200
        assert client.get("/api/admin/integrations/webhooks").status_code == 403
        assert client.get("/api/admin/integrations/webhooks/events").status_code == 403
        assert client.get("/api/admin/integrations/webhooks/summary").status_code == 403
        assert client.get("/api/admin/integrations/webhooks/deliveries/history").status_code == 403
        denied = client.post(
            "/api/admin/integrations/webhooks",
            json={
                "name": "Denied webhook",
                "endpoint_url": "http://bot.example.test/hooks/denied",
                "event_types": ["integration.test"],
            },
        )
        assert denied.status_code == 403


def test_webhook_dns_errors_are_reported_with_actionable_context() -> None:
    message = _delivery_transport_error(
        "https://royal-blackwater-fleet.eu/integrations/discord/webhooks/rbf",
        URLError(socket.gaierror(-3, "Temporary failure in name resolution")),
    )

    assert "DNS resolution failed" in message
    assert "royal-blackwater-fleet.eu" in message
    assert "API container outbound network" in message
