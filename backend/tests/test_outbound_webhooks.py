import json
import socket
from urllib.error import URLError

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
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
        assert payload["resource"]["url"] == (
            f"{settings.cors_origins[0].rstrip('/')}/calendar/events/42"
        )
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


def test_bot_event_catalog_has_stable_route_family_for_every_domain_event() -> None:
    from app.modules.admin.services.outbound_webhook_service import EVENT_CATALOG

    route_families = {
        "integration.test": ("default", "test"),
        "registration.request.": ("registrations", "registration_request"),
        "squad.": ("squads", "squad"),
        "calendar.": ("events", "calendar_event"),
        "guide.": ("guides", "guide"),
        "newcomer_guide.": ("guides", "guide"),
        "build.": ("builds", "build"),
        "forum.thread.": ("forum", "forum_thread"),
    }
    for event_type, _, _ in EVENT_CATALOG:
        assert any(event_type == prefix or event_type.startswith(prefix) for prefix in route_families), event_type


def test_discord_chat_webhook_renders_direct_payload_and_hides_token() -> None:
    from app.modules.admin.models.outbound_webhook import OutboundWebhook
    from app.modules.admin.services.outbound_webhook_delivery_service.service import WebhookDeliveryService

    class CaptureTransport:
        def __init__(self) -> None:
            self.request = None

        def send(self, request):
            self.request = request
            return 204, ""

        @staticmethod
        def error_message(endpoint_url, exc):
            return str(exc)

    with isolated_session() as db:
        actor = create_user(
            db,
            username="discord-chat-admin",
            password="BlackwaterDiscordChat123!",
            display_name="Discord Chat Admin",
            role=ROLE_ADMIN,
        )
        token = "discord-webhook-token-secret"
        created = create_webhook(
            db,
            OutboundWebhookCreate(
                name="Registration chat",
                endpoint_url=f"https://discord.com/api/webhooks/123456789012345678/{token}",
                event_types=["registration.request.created"],
                delivery_mode="discord",
                message_template=(
                    "New registration: {data.display_name}\n"
                    "[Review registration]({resource.url})"
                ),
                discord_username="RBF Hub",
            ),
            actor,
        )
        assert token not in created.endpoint_url
        assert created.signing_secret is None
        delivery_ids = queue_webhook_event(
            db,
            event_type="registration.request.created",
            resource_type="registration_request",
            resource_id=77,
            actor=actor,
            resource_url="/admin?tab=registrations",
            data={"display_name": "Test Captain", "username": "captain"},
        )
        delivery = db.get(OutboundWebhookDelivery, delivery_ids[0])
        webhook = db.get(OutboundWebhook, delivery.webhook_id)
        transport = CaptureTransport()
        WebhookDeliveryService(transport=transport)._deliver(delivery, webhook)
        payload = json.loads(transport.request.data.decode("utf-8"))
        public_url = f"{settings.cors_origins[0].rstrip('/')}/admin?tab=registrations"
        assert payload["content"] == (
            "New registration: Test Captain\n"
            f"[Review registration]({public_url})"
        )
        assert payload["content"].count(public_url) == 1
        assert payload["username"] == "RBF Hub"
        assert "X-rbf-signature" not in {key.lower() for key, _ in transport.request.header_items()}
        assert delivery.status == "success"


def test_webhook_scope_matching_supports_fleet_and_squad_destinations() -> None:
    from app.modules.admin.models.outbound_webhook import OutboundWebhook
    from app.modules.admin.services.outbound_webhook_delivery_service.service import WebhookDeliveryService

    fleet_hook = OutboundWebhook(scope_type="fleet", scope_id=12)
    squad_hook = OutboundWebhook(scope_type="squad", scope_id=34)
    assert WebhookDeliveryService._matches_scope(fleet_hook, {"fleet_id": 12})
    assert not WebhookDeliveryService._matches_scope(fleet_hook, {"fleet_id": 13})
    assert WebhookDeliveryService._matches_scope(squad_hook, {"squad_id": 34, "fleet_id": 12})
    assert not WebhookDeliveryService._matches_scope(squad_hook, {"squad_id": 35})


def test_default_build_messages_use_the_actual_build_name_field() -> None:
    from app.modules.admin.services.outbound_webhook_delivery_service.discord import render_message
    from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES

    envelope = {
        "event": "build.created",
        "destination": {"name": "Build channel"},
        "data": {"build_name": "Heavy Broadside", "name": "wrong-field"},
    }

    assert render_message(DEFAULT_MESSAGES["build.created"], envelope) == "Neuer Build: **Heavy Broadside**."
    assert "data.name" not in DEFAULT_MESSAGES["build.updated"]
    assert "data.build_name" in DEFAULT_MESSAGES["build.removed"]


def test_every_catalog_event_has_a_serializable_preview_payload() -> None:
    from app.modules.admin.schemas.outbound_webhook import OutboundWebhookCreate
    from app.modules.admin.services.webhook_events import EVENT_TEST_SAMPLES, event_test_sample

    with isolated_session() as db:
        actor = create_user(
            db,
            username="webhook-catalog-admin",
            password="BlackwaterWebhookCatalog123!",
            display_name="Webhook Catalog Admin",
            role=ROLE_ADMIN,
        )
        webhook = create_webhook(
            db,
            OutboundWebhookCreate(
                name="All event previews",
                endpoint_url="http://bot.example.test/hooks/all-events",
                event_types=sorted(EVENT_TEST_SAMPLES),
            ),
            actor,
        )
        for event_type in sorted(EVENT_TEST_SAMPLES):
            sample = event_test_sample(event_type)
            delivery_ids = queue_webhook_event(
                db,
                event_type=event_type,
                resource_type=sample["resource_type"],
                resource_id=sample["resource_id"],
                resource_url=sample.get("resource_url"),
                actor=actor,
                scope_type=sample.get("scope_type", "global"),
                scope_id=sample.get("scope_id"),
                fleet_id=sample.get("fleet_id"),
                squad_id=sample.get("squad_id"),
                data=sample["data"],
            )
            assert len(delivery_ids) == 1, event_type
            delivery = db.get(OutboundWebhookDelivery, delivery_ids[0])
            assert delivery is not None
            assert delivery.webhook_id == webhook.id
            payload = json.loads(delivery.payload_json)
            assert payload["event"] == event_type
            assert isinstance(payload["data"], dict)


def test_event_specific_preview_uses_the_real_event_payload_shape() -> None:
    from app.modules.admin.models.outbound_webhook import OutboundWebhook
    from app.modules.admin.services.outbound_webhook_delivery_service.envelope import (
        WebhookEnvelopeFactory,
    )

    with isolated_session() as db:
        actor = create_user(
            db,
            username="webhook-preview-admin",
            password="BlackwaterWebhookPreview123!",
            display_name="Webhook Preview Admin",
            role=ROLE_ADMIN,
        )
        webhook = OutboundWebhook(
            id=91,
            name="Build previews",
            endpoint_url="https://discord.com/api/webhooks/123/token",
            delivery_mode="discord",
            event_types_json='["build.created"]',
            created_by_user_id=actor.id,
            created_by_username=actor.username,
        )
        _, envelope = WebhookEnvelopeFactory().test(webhook, actor, "build.created")
        assert envelope["event"] == "build.created"
        assert envelope["data"]["build_name"] == "Heavy Broadside"
        assert envelope["data"]["ship"]["name"] == "Anson"
        assert envelope["resource"]["url"].endswith("/builds/401")


def test_build_create_update_and_remove_publish_real_webhook_deliveries(monkeypatch) -> None:
    from app.db.session import engine
    from app.modules.admin.services import outbound_webhook_delivery_service as delivery_module
    from app.modules.fleet.models.fleet import Fleet
    from app.modules.ships.models.ship import Ship
    from app.seeds.manager import SeedManager

    class CaptureTransport:
        def __init__(self) -> None:
            self.requests = []

        def send(self, request):
            self.requests.append(request)
            return 202, "accepted"

        @staticmethod
        def error_message(endpoint_url, exc):
            return str(exc)

    register_all_models()
    Base.metadata.create_all(engine)
    capture = CaptureTransport()
    monkeypatch.setattr(delivery_module._default_service, "_transport", capture)

    owner_username = "real-build-webhook-owner"
    owner_password = "RealBuildWebhookOwner123!"
    with SessionLocal() as db:
        seed = SeedManager(db)
        seed.seed_role_catalog()
        seed.seed_fleets()
        seed.seed_weapon_slot_types()
        seed.seed_ships()
        seed.seed_build_options()
        actor = create_user(
            db,
            username="real-build-webhook-admin",
            password="RealBuildWebhookAdmin123!",
            display_name="Real Build Webhook Admin",
            role=ROLE_ADMIN,
        )
        create_user(
            db,
            username=owner_username,
            password=owner_password,
            display_name="Real Build Webhook Owner",
        )
        ship = db.scalar(select(Ship).where(Ship.name == "Anson"))
        fleet = db.scalar(select(Fleet).where(Fleet.slug == "royal-blackwater-fleet"))
        assert ship is not None
        assert fleet is not None
        ship_id = ship.id
        fleet_id = fleet.id
        webhook = create_webhook(
            db,
            OutboundWebhookCreate(
                name="Real build events",
                endpoint_url="http://bot.example.test/hooks/real-builds",
                event_types=["build.created", "build.updated", "build.removed"],
                scope_type="fleet",
                scope_id=fleet_id,
                message_template="{event}: {data.build_name}",
            ),
            actor,
        )
        webhook_id = webhook.id

    payload = {
        "build_name": "Webhook Broadside",
        "build_type": "balanced",
        "ship_id": ship_id,
        "sailors": 80,
        "soldiers": 80,
    }
    with TestClient(app) as client:
        login = client.post(
            "/api/auth/login",
            json={"username": owner_username, "password": owner_password},
        )
        assert login.status_code == 200, login.text
        created = client.post("/api/builds", json=payload)
        assert created.status_code == 201, created.text
        build_id = created.json()["id"]

        updated_payload = {**payload, "build_name": "Webhook Broadside Mk II"}
        updated = client.put(f"/api/builds/mine/{build_id}", json=updated_payload)
        assert updated.status_code == 200, updated.text

        removed = client.delete(f"/api/builds/mine/{build_id}")
        assert removed.status_code == 204, removed.text

    with SessionLocal() as db:
        rows = list(
            db.scalars(
                select(OutboundWebhookDelivery)
                .where(OutboundWebhookDelivery.webhook_id == webhook_id)
                .order_by(OutboundWebhookDelivery.id.asc())
            ).all()
        )
        assert [row.event_type for row in rows] == [
            "build.created",
            "build.updated",
            "build.removed",
        ]
        assert all(row.status == "success" for row in rows)
        created_payload = json.loads(rows[0].payload_json)
        updated_payload_json = json.loads(rows[1].payload_json)
        removed_payload = json.loads(rows[2].payload_json)
        assert created_payload["data"]["build_name"] == "Webhook Broadside"
        assert created_payload["data"]["ship"]["name"] == "Anson"
        assert created_payload["scope"]["fleet_id"] == fleet_id
        assert updated_payload_json["data"]["build_name"] == "Webhook Broadside Mk II"
        assert removed_payload["data"] == {
            "id": build_id,
            "build_name": "Webhook Broadside Mk II",
        }
    assert len(capture.requests) == 3
