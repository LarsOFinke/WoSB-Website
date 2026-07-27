import json
import socket
from types import SimpleNamespace
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
from app.modules.admin.services.outbound_webhook_service import (
    _public_endpoint,
    _validate_endpoint_url,
    create_webhook,
)
from app.modules.registry import register_all_models
from main import app


def isolated_session() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_webhook_service_queues_matching_discord_delivery_payload() -> None:
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
                endpoint_url="https://discord.com/api/webhooks/111111111111111111/test-token-events",
                event_types=["calendar.event.created", "guide.created"],
                message_template="New event: {data.title}",
            ),
            actor,
        )
        assert created.endpoint_url.endswith("/••••••")

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
        assert payload["destination"]["scope_type"] == "global"
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


def test_admin_can_manage_discord_webhooks_and_token_stays_masked() -> None:
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
            "/api/admin/discord-webhooks",
            json={
                "name": "Discord guides",
                "endpoint_url": "https://discord.com/api/webhooks/222222222222222222/test-token-guides",
                "event_types": ["guide.created", "guide.updated"],
                "message_template": "{data.title}",
                "is_active": True,
            },
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["endpoint_url"].endswith("/••••••")
        assert "test-token-guides" not in body["endpoint_url"]
        webhook_id = body["id"]

        listing = client.get("/api/admin/discord-webhooks")
        assert listing.status_code == 200
        listed = next(row for row in listing.json() if row["id"] == webhook_id)
        assert listed["endpoint_url"].endswith("/••••••")
        assert listed["event_types"] == ["guide.created", "guide.updated"]

        updated = client.put(
            f"/api/admin/discord-webhooks/{webhook_id}",
            json={
                "name": "Discord guide updates",
                "endpoint_url": None,
                "event_types": ["guide.updated"],
                "scope_type": "global",
                "is_active": True,
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["name"] == "Discord guide updates"
        assert updated.json()["endpoint_url"].endswith("/••••••")

        deleted = client.delete(f"/api/admin/discord-webhooks/{webhook_id}")
        assert deleted.status_code == 204


def test_discord_webhook_url_accepts_copied_and_versioned_official_urls() -> None:
    copied = "<https://discord.com/api/webhooks/222222222222222222/copied-token>"
    versioned = "https://discord.com/api/v10/webhooks/222222222222222222/versioned-token"

    assert _validate_endpoint_url(copied) == copied[1:-1]
    assert _validate_endpoint_url(versioned) == versioned


def test_versioned_discord_webhook_url_is_masked_with_its_real_id() -> None:
    endpoint = "https://discord.com/api/v10/webhooks/222222222222222222/versioned-token"

    assert _public_endpoint(SimpleNamespace(endpoint_url=endpoint)) == (
        "https://discord.com/api/webhooks/222222222222222222/••••••"
    )


def test_admin_event_catalog_returns_the_versioned_english_repository_templates() -> None:
    username = "webhook-template-catalog-admin"
    password = "BlackwaterWebhookTemplates123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Webhook Template Catalog Admin",
                role=ROLE_ADMIN,
            )
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200

        response = client.get("/api/admin/discord-webhooks/events")
        assert response.status_code == 200
        catalog = {row["key"]: row["default_template"] for row in response.json()}
        build_template = catalog["build.created"]
        assert build_template.startswith("⚓ **New Build Created**")
        assert "Ship: **{data.ship.name}**" in build_template
        assert "Created by: **{actor.display_name}**" in build_template
        assert "[Open build]({resource.url})" in build_template
        assert "Neuer Build" not in build_template


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
        assert client.get("/api/admin/discord-webhooks").status_code == 403
        assert client.get("/api/admin/discord-webhooks/events").status_code == 403
        assert client.get("/api/admin/discord-webhooks/summary").status_code == 403
        assert client.get("/api/admin/discord-webhooks/broadcast/targets").status_code == 403
        assert client.get("/api/admin/discord-webhooks/deliveries/history").status_code == 403
        denied = client.post(
            "/api/admin/discord-webhooks",
            json={
                "name": "Denied webhook",
                "endpoint_url": "https://discord.com/api/webhooks/333333333333333333/denied-token",
                "event_types": ["integration.test"],
            },
        )
        assert denied.status_code == 403
        broadcast_denied = client.post(
            "/api/admin/discord-webhooks/broadcast/send",
            json={"webhook_ids": [1], "message": "Denied"},
        )
        assert broadcast_denied.status_code == 403


def test_webhook_dns_errors_are_reported_with_actionable_context() -> None:
    message = _delivery_transport_error(
        "https://discord.com/api/webhooks/444444444444444444/test-token",
        URLError(socket.gaierror(-3, "Temporary failure in name resolution")),
    )

    assert "DNS resolution failed" in message
    assert "discord.com" in message
    assert "API container outbound network" in message


def test_webhook_event_catalog_has_stable_route_family_for_every_domain_event() -> None:
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
                message_template=(
                    "New registration: {data.display_name}\n"
                    "[Review registration]({resource.url})"
                ),
                discord_username="RBF Hub",
            ),
            actor,
        )
        assert token not in created.endpoint_url
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
        assert "x-rbf-signature" not in {key.lower() for key, _ in transport.request.header_items()}
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


def test_default_build_messages_are_full_english_templates_with_deep_links() -> None:
    from app.modules.admin.services.outbound_webhook_delivery_service.discord import render_message
    from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES

    envelope = {
        "event": "build.created",
        "actor": {"display_name": "Build Captain"},
        "resource": {"url": "https://royal-blackwater-fleet.eu/builds/401"},
        "data": {
            "build_name": "Heavy Broadside",
            "build_type": "balanced",
            "ship": {"name": "Anson", "rate": 3},
            "is_official_template": False,
            "sailors": 90,
            "soldiers": 70,
            "musketeers": 0,
            "mercenaries": 0,
            "owner_id": 42,
            "created_at": "2026-08-15T12:00:00+00:00",
        },
    }

    rendered = render_message(DEFAULT_MESSAGES["build.created"], envelope)
    assert rendered.startswith("⚓ **New Build Created**")
    assert "Build: **Heavy Broadside**" in rendered
    assert "Ship: **Anson** (Rate `3`)" in rendered
    assert "Created by: **Build Captain**" in rendered
    assert "[Open build](https://royal-blackwater-fleet.eu/builds/401)" in rendered
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
                endpoint_url="https://discord.com/api/webhooks/555555555555555555/all-events-token",
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
    from app.bootstrap.manager import SeedManager

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
                endpoint_url="https://discord.com/api/webhooks/666666666666666666/real-build-token",
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


def test_same_event_can_queue_deliveries_for_multiple_discord_channels() -> None:
    from app.modules.admin.models.outbound_webhook import OutboundWebhook

    with isolated_session() as db:
        actor = create_user(
            db,
            username="webhook-multi-channel-admin",
            password="BlackwaterMultiChannel123!",
            display_name="Webhook Multi Channel Admin",
            role=ROLE_ADMIN,
        )
        first = create_webhook(
            db,
            OutboundWebhookCreate(
                name="Build announcements",
                endpoint_url="https://discord.com/api/webhooks/700000000000000001/first-channel-token",
                event_types=["build.created"],
            ),
            actor,
        )
        second = create_webhook(
            db,
            OutboundWebhookCreate(
                name="Officer build log",
                endpoint_url="https://discord.com/api/webhooks/700000000000000002/second-channel-token",
                event_types=["build.created"],
            ),
            actor,
        )

        delivery_ids = queue_webhook_event(
            db,
            event_type="build.created",
            resource_type="build",
            resource_id=501,
            actor=actor,
            data={"id": 501, "build_name": "Multi-channel Broadside"},
        )

        rows = list(
            db.scalars(
                select(OutboundWebhookDelivery)
                .where(OutboundWebhookDelivery.id.in_(delivery_ids))
                .order_by(OutboundWebhookDelivery.webhook_id.asc())
            ).all()
        )
        assert len(rows) == 2
        assert {row.webhook_id for row in rows} == {first.id, second.id}
        assert {
            db.get(OutboundWebhook, row.webhook_id).name for row in rows
        } == {"Build announcements", "Officer build log"}


def test_admin_can_send_one_manual_broadcast_to_multiple_discord_channels(monkeypatch) -> None:
    from app.modules.admin.services import outbound_webhook_delivery_service as delivery_module

    class CaptureTransport:
        def __init__(self) -> None:
            self.requests = []

        def send(self, request):
            self.requests.append(request)
            return 204, ""

        @staticmethod
        def error_message(endpoint_url, exc):
            return str(exc)

    username = "webhook-broadcast-admin"
    password = "BlackwaterBroadcast123!"
    transport = CaptureTransport()
    monkeypatch.setattr(delivery_module._default_service, "_transport", transport)

    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Webhook Broadcast Admin",
                role=ROLE_ADMIN,
            )
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200

        target_ids = []
        for index in range(2):
            created = client.post(
                "/api/admin/discord-webhooks",
                json={
                    "name": f"Broadcast channel {index + 1}",
                    "endpoint_url": (
                        f"https://discord.com/api/webhooks/80000000000000000{index + 1}/"
                        f"broadcast-channel-token-{index + 1}"
                    ),
                    "event_types": [],
                    "broadcast_enabled": True,
                    "is_active": True,
                },
            )
            assert created.status_code == 201, created.text
            target_ids.append(created.json()["id"])

        event_only = client.post(
            "/api/admin/discord-webhooks",
            json={
                "name": "Event only channel",
                "endpoint_url": "https://discord.com/api/webhooks/800000000000000003/event-only-token",
                "event_types": ["build.created"],
                "broadcast_enabled": False,
                "is_active": True,
            },
        )
        assert event_only.status_code == 201, event_only.text

        targets = client.get("/api/admin/discord-webhooks/broadcast/targets")
        assert targets.status_code == 200, targets.text
        returned_ids = {row["id"] for row in targets.json()}
        assert set(target_ids).issubset(returned_ids)
        assert event_only.json()["id"] not in returned_ids

        sent = client.post(
            "/api/admin/discord-webhooks/broadcast/send",
            json={
                "webhook_ids": target_ids,
                "message": "**Fleet broadcast**\nPrepare for departure.",
                "discord_username": "RBF Broadcast",
                "discord_avatar_url": "https://royal-blackwater-fleet.eu/rbf-fleet-icon.png?v=test",
            },
        )
        assert sent.status_code == 200, sent.text
        deliveries = sent.json()
        assert len(deliveries) == 2
        assert all(row["event_type"] == "broadcast.manual" for row in deliveries)
        assert all(row["status"] == "queued" for row in deliveries)
        delivery_ids = [row["id"] for row in deliveries]

    with SessionLocal() as db:
        persisted = [db.get(OutboundWebhookDelivery, delivery_id) for delivery_id in delivery_ids]
        assert all(row is not None and row.status == "success" for row in persisted)

    assert len(transport.requests) == 2
    for request in transport.requests:
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["content"] == "**Fleet broadcast**\nPrepare for departure."
        assert payload["username"] == "RBF Broadcast"
        assert payload["avatar_url"].endswith("?v=test")
        assert payload["allowed_mentions"] == {"parse": []}


def test_broadcast_requires_active_broadcast_enabled_targets(monkeypatch) -> None:
    from app.modules.admin.services import outbound_webhook_delivery_service as delivery_module

    class NoopTransport:
        def send(self, request):
            raise AssertionError("Disabled target must not be called")

        @staticmethod
        def error_message(endpoint_url, exc):
            return str(exc)

    username = "webhook-broadcast-validation-admin"
    password = "BlackwaterBroadcastValidation123!"
    monkeypatch.setattr(delivery_module._default_service, "_transport", NoopTransport())

    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Webhook Broadcast Validation Admin",
                role=ROLE_ADMIN,
            )
        assert client.post(
            "/api/auth/login", json={"username": username, "password": password}
        ).status_code == 200
        created = client.post(
            "/api/admin/discord-webhooks",
            json={
                "name": "Non-broadcast target",
                "endpoint_url": "https://discord.com/api/webhooks/900000000000000001/non-broadcast-token",
                "event_types": ["integration.test"],
                "broadcast_enabled": False,
            },
        )
        assert created.status_code == 201, created.text
        response = client.post(
            "/api/admin/discord-webhooks/broadcast/send",
            json={"webhook_ids": [created.json()["id"]], "message": "Must fail"},
        )
        assert response.status_code == 400
        assert "broadcast-enabled" in response.json()["detail"]


def test_stale_processing_webhook_delivery_is_recovered_once(tmp_path) -> None:
    from datetime import timedelta

    from sqlalchemy.orm import sessionmaker

    from app.core.time import utc_now
    from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery
    from app.modules.admin.services.outbound_webhook_delivery_service.service import (
        WebhookDeliveryService,
    )

    class CaptureTransport:
        def __init__(self) -> None:
            self.calls = 0

        def send(self, request):
            self.calls += 1
            return 204, ""

        @staticmethod
        def error_message(endpoint_url, exc):
            return str(exc)

    register_all_models()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'webhook-recovery.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as db:
        actor = create_user(
            db,
            username="webhook-recovery-admin",
            password="BlackwaterWebhookRecovery123!",
            display_name="Webhook Recovery Admin",
            role=ROLE_ADMIN,
        )
        create_webhook(
            db,
            OutboundWebhookCreate(
                name="Recovery target",
                endpoint_url="https://discord.com/api/webhooks/666666666666666666/recovery-token",
                event_types=["build.created"],
            ),
            actor,
        )
        delivery_id = queue_webhook_event(
            db,
            event_type="build.created",
            resource_type="build",
            resource_id=91,
            actor=actor,
            data={"id": 91, "build_name": "Recovered build"},
        )[0]
        fresh_delivery_id = queue_webhook_event(
            db,
            event_type="build.created",
            resource_type="build",
            resource_id=92,
            actor=actor,
            data={"id": 92, "build_name": "Active delivery"},
        )[0]
        delivery = db.get(OutboundWebhookDelivery, delivery_id)
        delivery.status = "processing"
        delivery.attempts = 1
        delivery.last_attempt_at = utc_now() - timedelta(minutes=10)
        fresh_delivery = db.get(OutboundWebhookDelivery, fresh_delivery_id)
        fresh_delivery.status = "processing"
        fresh_delivery.attempts = 1
        fresh_delivery.last_attempt_at = utc_now()
        db.commit()

    transport = CaptureTransport()
    service = WebhookDeliveryService(
        session_factory=session_factory,
        transport=transport,
    )

    assert service.recover_pending(stale_after=timedelta(minutes=5)) == 1
    assert transport.calls == 1

    with session_factory() as db:
        delivery = db.get(OutboundWebhookDelivery, delivery_id)
        assert delivery.status == "success"
        assert delivery.attempts == 2
        fresh_delivery = db.get(OutboundWebhookDelivery, fresh_delivery_id)
        assert fresh_delivery.status == "processing"
        assert fresh_delivery.attempts == 1

    service.attempt(delivery_id)
    assert transport.calls == 1
