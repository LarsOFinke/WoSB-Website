from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from app.modules.calendar.models.fleet_event import FleetEvent
from app.modules.calendar.schemas.fleet_event_create import FleetEventCreate
from app.modules.calendar.services.fleet_event_service import create_fleet_event
from app.modules.fleet.models.fleet import Fleet
from app.modules.raid_helper.models.raid_helper import RaidHelperEventLink, RaidHelperProfile
from app.modules.raid_helper.schemas.raid_helper import (
    RaidHelperDestinationWrite,
    RaidHelperDispatchSelection,
    RaidHelperProfileCreate,
    RaidHelperTemplateWrite,
)
from app.modules.raid_helper.services import raid_helper_service
from app.modules.squads.models.squad import Squad
from main import app


def _profile(db, admin):
    return raid_helper_service.create_profile(
        db,
        RaidHelperProfileCreate(
            name="Raid Helper Test Profile",
            server_id="123456789012345678",
            api_key="super-secret-raid-key",
            timezone="Europe/Berlin",
        ),
        admin,
    )


def test_raid_helper_profiles_are_admin_only_and_keys_are_encrypted() -> None:
    with TestClient(app) as client:
        assert client.get("/api/admin/raid-helper/profiles").status_code == 401
        with SessionLocal() as db:
            admin = create_user(
                db,
                username="raid-helper-admin",
                password="RaidHelperAdminPassword123!",
                display_name="Raid Helper Admin",
                role=ROLE_ADMIN,
            )
            created = _profile(db, admin)
            stored = db.get(RaidHelperProfile, created.id)
            assert stored is not None
            assert "super-secret-raid-key" not in stored.api_key_encrypted
            assert created.api_key_configured is True
            assert not hasattr(created, "api_key")

        login = client.post(
            "/api/auth/login",
            json={"username": "raid-helper-admin", "password": "RaidHelperAdminPassword123!"},
        )
        assert login.status_code == 200
        response = client.get("/api/admin/raid-helper/profiles")
        assert response.status_code == 200
        assert response.json()[0]["api_key_configured"] is True
        assert "api_key" not in response.json()[0]


def test_scope_category_filter_and_delivery_payload(monkeypatch) -> None:
    with TestClient(app):
        with SessionLocal() as db:
            admin = db.scalar(select(RaidHelperProfile).limit(1))
            # The first test may not run before this one, so create an independent administrator/profile.
            user = create_user(
                db,
                username="raid-helper-routing-admin",
                password="RaidHelperRoutingPassword123!",
                display_name="Routing Admin",
                role=ROLE_ADMIN,
            )
            profile = raid_helper_service.create_profile(
                db,
                RaidHelperProfileCreate(
                    name="Raid Helper Routing Profile",
                    server_id="223456789012345678",
                    api_key="routing-secret-key",
                    timezone="Europe/Berlin",
                ),
                user,
            )
            fleet = db.scalar(select(Fleet).order_by(Fleet.id).limit(1))
            if fleet is None:
                fleet = Fleet(
                    name="Raid Helper Fleet",
                    slug="raid-helper-fleet",
                    focus="mixed",
                    description="Raid Helper test fleet",
                    sort_order=10,
                )
                db.add(fleet)
                db.flush()
            squad = Squad(
                fleet_id=fleet.id,
                name="Raid Helper Squad",
                slug="raid-helper-squad",
                created_by_id=user.id,
            )
            db.add(squad)
            db.commit()
            db.refresh(squad)

            fleet_destination = raid_helper_service.save_destination(
                db,
                RaidHelperDestinationWrite(
                    profile_id=profile.id,
                    name="Fleet operations channel",
                    channel_id="323456789012345678",
                    scope_type="fleet",
                    categories=["operation"],
                    is_default=True,
                ),
            )
            squad_destination = raid_helper_service.save_destination(
                db,
                RaidHelperDestinationWrite(
                    profile_id=profile.id,
                    name="Squad training channel",
                    channel_id="423456789012345678",
                    scope_type="squad",
                    squad_id=squad.id,
                    categories=["training"],
                    is_default=True,
                ),
            )
            fleet_template = raid_helper_service.save_template(
                db,
                RaidHelperTemplateWrite(
                    profile_id=profile.id,
                    name="Fleet operation template",
                    raid_template_id="fleet-operation",
                    scope_type="fleet",
                    categories=["operation"],
                    title_template="{{scope.name}}: {{event.title}}",
                    description_template="{{event.description}}",
                    announcement_template="{{event.category}}",
                    is_default=True,
                ),
            )
            raid_helper_service.save_template(
                db,
                RaidHelperTemplateWrite(
                    profile_id=profile.id,
                    name="Squad training template",
                    raid_template_id="squad-training",
                    scope_type="squad",
                    categories=["training"],
                    is_default=True,
                ),
            )

            fleet_options = raid_helper_service.integration_options(
                db, user, category="operation", squad_id=None
            )
            assert [row.id for row in fleet_options] == [fleet_destination.id]
            assert [row.id for row in fleet_options[0].templates] == [fleet_template.id]
            squad_options = raid_helper_service.integration_options(
                db, user, category="training", squad_id=squad.id
            )
            assert [row.id for row in squad_options] == [squad_destination.id]
            assert raid_helper_service.integration_options(
                db, user, category="meeting", squad_id=squad.id
            ) == []

            start = datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc)
            event = create_fleet_event(
                db,
                FleetEventCreate(
                    title="Fleet assault",
                    category="operation",
                    description="Line up at the harbor.",
                    location="Fleet voice",
                    start_at=start,
                    end_at=start + timedelta(hours=2),
                    all_day=False,
                    squad_id=None,
                    raid_helper_enabled=True,
                    raid_helper_dispatches=[
                        RaidHelperDispatchSelection(
                            destination_id=fleet_destination.id,
                            template_id=fleet_template.id,
                        )
                    ],
                ),
                user,
            )
            assert len(event.raid_helper_links) == 1
            link = db.scalar(
                select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event.id)
            )
            assert link is not None

            requests: list[tuple[str, str, dict | None]] = []

            def fake_request(profile_row, method, path, payload=None):
                requests.append((method, path, payload))
                return 201, {"eventId": "987654321098765432"}

            monkeypatch.setattr(raid_helper_service, "_request", fake_request)
            raid_helper_service._sync_link(db, link)

            assert requests[0][0] == "POST"
            assert requests[0][1] == (
                "/servers/223456789012345678/channels/323456789012345678/event"
            )
            assert requests[0][2]["title"] == "Fleet: Fleet assault"
            assert requests[0][2]["date"] == "2026-08-01"
            assert requests[0][2]["time"] == "20:00"
            assert requests[0][2]["duration"] == 120
            assert requests[0][2]["date_variant"] == "both"
            assert requests[0][2]["12h_format"] is False
            assert requests[0][2]["info_variant"] == "long"
            assert requests[0][2]["preserve_order"] is True
            assert requests[0][2]["apply_unregister"] is True
            assert link.external_event_id == "987654321098765432"
            assert link.status == "delivered"


def test_cancelled_unsent_event_is_not_created_remotely(monkeypatch) -> None:
    with TestClient(app):
        with SessionLocal() as db:
            user = create_user(
                db,
                username="raid-helper-cancel-admin",
                password="RaidHelperCancelPassword123!",
                display_name="Cancel Admin",
                role=ROLE_ADMIN,
            )
            profile = raid_helper_service.create_profile(
                db,
                RaidHelperProfileCreate(
                    name="Raid Helper Cancellation Profile",
                    server_id="523456789012345678",
                    api_key="cancel-secret-key",
                    timezone="Europe/Berlin",
                ),
                user,
            )
            destination = raid_helper_service.save_destination(
                db,
                RaidHelperDestinationWrite(
                    profile_id=profile.id,
                    name="Cancellation channel",
                    channel_id="623456789012345678",
                    scope_type="fleet",
                    categories=["operation"],
                    is_default=True,
                ),
            )
            template = raid_helper_service.save_template(
                db,
                RaidHelperTemplateWrite(
                    profile_id=profile.id,
                    name="Cancellation template",
                    raid_template_id="cancel-operation",
                    scope_type="fleet",
                    categories=["operation"],
                    is_default=True,
                ),
            )
            start = datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc)
            event = create_fleet_event(
                db,
                FleetEventCreate(
                    title="Cancelled before delivery",
                    category="operation",
                    description="This event must never be created remotely.",
                    location="Fleet voice",
                    start_at=start,
                    end_at=start + timedelta(hours=1),
                    all_day=False,
                    squad_id=None,
                    raid_helper_enabled=True,
                    raid_helper_dispatches=[
                        RaidHelperDispatchSelection(
                            destination_id=destination.id,
                            template_id=template.id,
                        )
                    ],
                ),
                user,
            )
            event_id = event.id
            link_id = event.raid_helper_links[0].id

        monkeypatch.setattr(
            raid_helper_service,
            "_request",
            lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remote request")),
        )
        raid_helper_service.sync_event(event_id, "cancel")
        with SessionLocal() as db:
            assert db.get(RaidHelperEventLink, link_id) is None


def test_raid_helper_requests_reuse_hardened_runtime_transport(monkeypatch) -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.request = None

        def send(self, request):
            self.request = request
            return 201, '{"eventId":"123456789012345678"}'

    with TestClient(app):
        with SessionLocal() as db:
            user = create_user(
                db,
                username="raid-helper-transport-admin",
                password="RaidHelperTransportPassword123!",
                display_name="Transport Admin",
                role=ROLE_ADMIN,
            )
            created = raid_helper_service.create_profile(
                db,
                RaidHelperProfileCreate(
                    name="Raid Helper Transport Profile",
                    server_id="723456789012345678",
                    api_key="transport-secret-key",
                    timezone="Europe/Berlin",
                ),
                user,
            )
            profile = db.get(RaidHelperProfile, created.id)
            assert profile is not None

            transport = FakeTransport()
            monkeypatch.setattr(raid_helper_service, "_RAID_HELPER_TRANSPORT", transport)
            status_code, body = raid_helper_service._request(
                profile,
                "POST",
                "/servers/723456789012345678/channels/823456789012345678/event",
                {"title": "Transport test"},
            )

            assert status_code == 201
            assert body == {"eventId": "123456789012345678"}
            assert transport.request is not None
            assert transport.request.get_method() == "POST"
            assert transport.request.full_url.endswith(
                "/servers/723456789012345678/channels/823456789012345678/event"
            )
            assert transport.request.data == b'{"title":"Transport test"}'
            assert transport.request.get_header("Authorization") == "transport-secret-key"
            assert transport.request.get_header("User-agent") == (
                "RoyalBlackwaterFleet-RaidHelper/1.0"
            )


def test_raid_helper_runtime_service_has_no_httpx_dependency() -> None:
    service_path = (
        Path(__file__).resolve().parents[1]
        / "src/app/modules/raid_helper/services/raid_helper_service.py"
    )
    source = service_path.read_text(encoding="utf-8")
    assert "import httpx" not in source
    assert "WebhookTransport" in source


def test_raid_helper_api_host_is_canonicalized() -> None:
    from app.modules.raid_helper.services.raid_helper_configuration import _validate_base_url

    assert _validate_base_url("https://raid-helper.dev/api/v4") == (
        "https://raid-helper.xyz/api/v4"
    )
    assert _validate_base_url("https://www.raid-helper.xyz/api/v4") == (
        "https://raid-helper.xyz/api/v4"
    )


def test_raid_helper_payload_preserves_exact_placeholder_types() -> None:
    context = {
        "event": {"duration_minutes": 90},
        "raid_helper": {"template_id": "123456789012345678"},
    }

    payload = raid_helper_service._render_json(
        {
            "duration": "{{event.duration_minutes}}",
            "templateId": "{{raid_helper.template_id}}",
            "label": "Template {{raid_helper.template_id}}",
        },
        context,
    )

    assert payload == {
        "duration": 90,
        "templateId": "123456789012345678",
        "label": "Template 123456789012345678",
    }


def test_raid_helper_http_error_reason_is_bounded_and_safe() -> None:
    assert raid_helper_service._failed_request_message(
        400,
        {"message": "  Invalid   templateId  "},
    ) == "Raid-Helper returned HTTP 400. Invalid templateId"
    assert raid_helper_service._failed_request_message(
        400,
        {"private": {"request": "must not leak"}},
    ) == "Raid-Helper returned HTTP 400."


def test_failed_raid_helper_delivery_can_be_retried(monkeypatch) -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            user = create_user(
                db,
                username="raid-helper-retry-admin",
                password="RaidHelperRetryPassword123!",
                display_name="Retry Admin",
                role=ROLE_ADMIN,
            )
            profile = raid_helper_service.create_profile(
                db,
                RaidHelperProfileCreate(
                    name="Raid Helper Retry Profile",
                    server_id="523456789012345678",
                    api_key="retry-secret-key",
                    timezone="Europe/Berlin",
                ),
                user,
            )
            destination = raid_helper_service.save_destination(
                db,
                RaidHelperDestinationWrite(
                    profile_id=profile.id,
                    name="Retry channel",
                    channel_id="623456789012345678",
                    scope_type="fleet",
                    categories=["operation"],
                    is_default=True,
                ),
            )
            template = raid_helper_service.save_template(
                db,
                RaidHelperTemplateWrite(
                    profile_id=profile.id,
                    name="Retry template",
                    raid_template_id="123456789012345678",
                    scope_type="fleet",
                    categories=["operation"],
                    is_default=True,
                ),
            )
            start = datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc)
            event = create_fleet_event(
                db,
                FleetEventCreate(
                    title="Retry operation",
                    category="operation",
                    start_at=start,
                    end_at=start + timedelta(hours=1),
                    all_day=False,
                    squad_id=None,
                    raid_helper_enabled=True,
                    raid_helper_dispatches=[
                        RaidHelperDispatchSelection(
                            destination_id=destination.id,
                            template_id=template.id,
                        )
                    ],
                ),
                user,
            )
            event_id = event.id
            link = db.scalar(
                select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event_id)
            )
            assert link is not None
            link.status = "failed"
            link.error_message = "Raid-Helper returned HTTP 400. Invalid templateId"
            db.commit()

        login = client.post(
            "/api/auth/login",
            json={
                "username": "raid-helper-retry-admin",
                "password": "RaidHelperRetryPassword123!",
            },
        )
        assert login.status_code == 200

        requests: list[dict] = []

        def fake_request(profile_row, method, path, payload=None):
            requests.append(payload)
            return 201, {"eventId": "112233445566778899"}

        monkeypatch.setattr(raid_helper_service, "_request", fake_request)
        response = client.post(f"/api/calendar/events/{event_id}/raid-helper/retry", json={})
        assert response.status_code == 200

        with SessionLocal() as db:
            link = db.scalar(
                select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event_id)
            )
            assert link is not None
            assert link.status == "delivered"
            assert link.external_event_id == "112233445566778899"
            assert requests[0]["templateId"] == "123456789012345678"
