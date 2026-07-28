from __future__ import annotations

import json
from importlib import import_module

from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery
from app.modules.admin.schemas.outbound_webhook import OutboundWebhookCreate
from app.modules.admin.services.outbound_webhook_service import create_webhook
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def test_group_search_actions_publish_versioned_webhook_events(monkeypatch) -> None:
    routes = import_module("app.modules.groups.routes.router")
    monkeypatch.setattr(routes, "schedule_webhook_deliveries", lambda *_: None)

    owner_username = "group-webhook-owner"
    owner_password = "BlackwaterGroupOwner123!"
    member_username = "group-webhook-member"
    member_password = "BlackwaterGroupMember123!"

    with TestClient(app) as client:
        with SessionLocal() as db:
            owner = create_user(
                db,
                username=owner_username,
                password=owner_password,
                display_name="Group Owner",
                role=ROLE_ADMIN,
            )
            create_user(
                db,
                username=member_username,
                password=member_password,
                display_name="Joining Captain",
            )
            create_webhook(
                db,
                OutboundWebhookCreate(
                    name="Group search events",
                    endpoint_url="https://discord.com/api/webhooks/333333333333333333/group-search-token",
                    event_types=["group.created", "group.member.joined", "group.closed"],
                ),
                owner,
            )

        _login(client, owner_username, owner_password)
        created = client.post(
            "/api/groups",
            json={
                "title": "Evening PvP group",
                "focus": "pvp_open_world",
                "max_members": 8,
                "min_ship_rate": 5,
                "max_ship_rate": 2,
                "allow_guests": True,
            },
        )
        assert created.status_code == 201, created.text
        group_id = created.json()["id"]

        assert client.post("/api/auth/logout").status_code == 204
        _login(client, member_username, member_password)
        joined = client.post(
            f"/api/groups/{group_id}/join",
            json={
                "display_name": "Joining Captain",
                "fleet_name": "Royal Blackwater Fleet",
                "ship_name": "De Zeven Provincien",
                "ship_rate": 3,
            },
        )
        assert joined.status_code == 200, joined.text

        assert client.post("/api/auth/logout").status_code == 204
        _login(client, owner_username, owner_password)
        closed = client.post(f"/api/groups/{group_id}/close")
        assert closed.status_code == 204, closed.text

        with SessionLocal() as db:
            deliveries = list(
                db.scalars(
                    select(OutboundWebhookDelivery)
                    .where(OutboundWebhookDelivery.resource_type == "group")
                    .where(OutboundWebhookDelivery.resource_id == group_id)
                    .order_by(OutboundWebhookDelivery.id)
                ).all()
            )
            assert [row.event_type for row in deliveries] == [
                "group.created",
                "group.member.joined",
                "group.closed",
            ]
            payloads = [json.loads(row.payload_json) for row in deliveries]
            assert payloads[0]["data"]["title"] == "Evening PvP group"
            assert "contact_note" not in payloads[0]["data"]
            member_payload = payloads[1]["data"]["member"]
            assert member_payload["display_name"] == "Joining Captain"
            assert member_payload["fleet_name"] == "Royal Blackwater Fleet"
            assert member_payload["ship_name"] == "De Zeven Provincien"
            assert member_payload["ship_rate"] == 3
            assert member_payload["is_guest"] is False
            assert "note" not in member_payload
            assert payloads[2]["data"]["status"] == "closed"


def test_closing_an_already_closed_group_does_not_publish_duplicate_event(monkeypatch) -> None:
    routes = import_module("app.modules.groups.routes.router")
    monkeypatch.setattr(routes, "schedule_webhook_deliveries", lambda *_: None)

    username = "group-close-idempotent"
    password = "BlackwaterGroupClose123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            owner = create_user(
                db,
                username=username,
                password=password,
                display_name="Group Close Owner",
                role=ROLE_ADMIN,
            )
            webhook = create_webhook(
                db,
                OutboundWebhookCreate(
                    name="Group close event",
                    endpoint_url="https://discord.com/api/webhooks/444444444444444444/group-close-token",
                    event_types=["group.closed"],
                ),
                owner,
            )
            webhook_id = webhook.id

        _login(client, username, password)
        created = client.post(
            "/api/groups",
            json={"title": "Close once", "focus": "pve_general", "max_members": 3},
        )
        assert created.status_code == 201, created.text
        group_id = created.json()["id"]
        assert client.post(f"/api/groups/{group_id}/close").status_code == 204
        assert client.post(f"/api/groups/{group_id}/close").status_code == 204

        with SessionLocal() as db:
            rows = list(
                db.scalars(
                    select(OutboundWebhookDelivery)
                    .where(OutboundWebhookDelivery.event_type == "group.closed")
                    .where(OutboundWebhookDelivery.resource_id == group_id)
                    .where(OutboundWebhookDelivery.webhook_id == webhook_id)
                ).all()
            )
            assert len(rows) == 1


def test_group_search_event_scope_is_derived_from_listing_owner(monkeypatch) -> None:
    routes = import_module("app.modules.groups.routes.router")
    captured: dict[str, object] = {}

    owner = type("Owner", (), {"fleet_id": 17})()

    class DbStub:
        def get(self, model, object_id):
            assert model.__name__ == "User"
            assert object_id == 42
            return owner

    def capture_queue(_db, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(routes, "queue_webhook_event_safely", capture_queue)
    monkeypatch.setattr(routes, "schedule_webhook_deliveries", lambda *_: None)

    group = type(
        "GroupPayload",
        (),
        {
            "id": 901,
            "owner_id": 42,
            "title": "Owner fleet group",
            "focus": "pvp_general",
            "status": "open",
            "max_members": 8,
            "active_members_count": 2,
            "spots_left": 6,
            "min_ship_rate": 5,
            "max_ship_rate": 2,
            "allow_guests": True,
            "fleet_restriction": None,
            "scheduled_start_at": None,
            "scheduled_end_at": None,
            "expires_at": None,
            "owner": type("OwnerRef", (), {"id": 42, "display_name": "Owner"})(),
        },
    )()
    joining_actor = type("Actor", (), {"fleet_id": 99})()

    routes._queue_group_event(
        BackgroundTasks(),
        DbStub(),
        "group.member.joined",
        group,
        joining_actor,
    )

    assert captured["scope_type"] == "fleet"
    assert captured["scope_id"] == 17
    assert captured["fleet_id"] == 17
