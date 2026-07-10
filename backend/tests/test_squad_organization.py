from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_USER
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.services.fleet_service import assign_fleet_role
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def _event_payload(*, squad_id: int | None, title: str) -> dict[str, object]:
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=2)
    return {
        "title": title,
        "category": "training",
        "description": "Squad readiness drill.",
        "location": "Squad voice channel",
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=2)).isoformat(),
        "all_day": False,
        "squad_id": squad_id,
    }


def test_squad_leadership_and_private_calendar_scope() -> None:
    passwords = {
        "admin": "BlackwaterSquadAdmin123!",
        "leader": "BlackwaterSquadLeader123!",
        "officer": "BlackwaterSquadOfficer123!",
        "member": "BlackwaterSquadMember123!",
        "outsider": "BlackwaterSquadOutsider123!",
    }

    with TestClient(app) as client:
        with SessionLocal() as db:
            fleet = db.query(Fleet).order_by(Fleet.id).first()
            if fleet is None:
                fleet = Fleet(
                    name="Royal Blackwater Fleet",
                    slug="royal-blackwater-fleet",
                    focus="mixed",
                    description="Squad organization fixture",
                    standing_orders="Organize below fleet command.",
                    sort_order=10,
                )
                db.add(fleet)
                db.commit()
                db.refresh(fleet)

            users = {
                "admin": create_user(
                    db,
                    username="squad-org-admin",
                    password=passwords["admin"],
                    display_name="Squad Admin",
                    role=ROLE_ADMIN,
                ),
                "leader": create_user(
                    db,
                    username="squad-org-leader",
                    password=passwords["leader"],
                    display_name="Squad Leader",
                    role=ROLE_USER,
                ),
                "officer": create_user(
                    db,
                    username="squad-org-officer",
                    password=passwords["officer"],
                    display_name="Squad Officer",
                    role=ROLE_USER,
                ),
                "member": create_user(
                    db,
                    username="squad-org-member",
                    password=passwords["member"],
                    display_name="Squad Member",
                    role=ROLE_USER,
                ),
                "outsider": create_user(
                    db,
                    username="squad-org-outsider",
                    password=passwords["outsider"],
                    display_name="Fleet Outsider",
                    role=ROLE_USER,
                ),
            }
            memberships = {
                key: assign_fleet_role(db, fleet.id, user.id, "member")
                for key, user in users.items()
                if key != "admin"
            }

        _login(client, users["outsider"].username, passwords["outsider"])
        denied = client.post(
            "/api/squads",
            json={
                "name": "Denied Squadron",
                "description": "Should not be created.",
                "leader_membership_id": memberships["leader"].id,
            },
        )
        assert denied.status_code == 403, denied.text
        _logout(client)

        _login(client, users["admin"].username, passwords["admin"])
        created = client.post(
            "/api/squads",
            json={
                "name": "Black Tide Squadron",
                "description": "A permanent combat unit inside the fleet.",
                "focus": "Port battles and coordinated line fighting",
                "max_members": 12,
                "leader_membership_id": memberships["leader"].id,
            },
        )
        assert created.status_code == 201, created.text
        squad = created.json()
        squad_id = squad["id"]
        assert squad["leader"]["display_name"] == "Squad Leader"
        assert squad["can_administer"] is True

        added_officer = client.post(
            f"/api/squads/{squad_id}/members",
            json={"fleet_membership_id": memberships["officer"].id, "role": "officer"},
        )
        assert added_officer.status_code == 201, added_officer.text
        officer_row = next(row for row in added_officer.json()["members"] if row["display_name"] == "Squad Officer")

        added_member = client.post(
            f"/api/squads/{squad_id}/members",
            json={"fleet_membership_id": memberships["member"].id, "role": "member"},
        )
        assert added_member.status_code == 201, added_member.text

        fleet_event = client.post(
            "/api/calendar/events",
            json=_event_payload(squad_id=None, title="Fleet-wide briefing"),
        )
        assert fleet_event.status_code == 201, fleet_event.text
        _logout(client)

        _login(client, users["leader"].username, passwords["leader"])
        updated = client.put(
            f"/api/squads/{squad_id}",
            json={"focus": "Port battles, screening and line command"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["can_administer"] is True

        squad_event = client.post(
            "/api/calendar/events",
            json=_event_payload(squad_id=squad_id, title="Black Tide drill"),
        )
        assert squad_event.status_code == 201, squad_event.text
        squad_event_id = squad_event.json()["id"]
        assert squad_event.json()["squad"]["name"] == "Black Tide Squadron"

        forbidden_fleet_event = client.post(
            "/api/calendar/events",
            json=_event_payload(squad_id=None, title="Unauthorized fleet event"),
        )
        assert forbidden_fleet_event.status_code == 403, forbidden_fleet_event.text
        _logout(client)

        _login(client, users["officer"].username, passwords["officer"])
        officer_detail = client.get(f"/api/squads/{squad_id}")
        assert officer_detail.status_code == 200
        assert officer_detail.json()["can_manage"] is True
        assert officer_detail.json()["can_administer"] is False

        escalation = client.put(
            f"/api/squads/{squad_id}/members/{officer_row['id']}",
            json={"role": "leader"},
        )
        assert escalation.status_code == 403, escalation.text

        officer_event = client.post(
            "/api/calendar/events",
            json=_event_payload(squad_id=squad_id, title="Officer-led practice"),
        )
        assert officer_event.status_code == 201, officer_event.text
        _logout(client)

        _login(client, users["member"].username, passwords["member"])
        member_events = client.get("/api/calendar/events")
        assert member_events.status_code == 200
        member_titles = {row["title"] for row in member_events.json()}
        assert {"Fleet-wide briefing", "Black Tide drill", "Officer-led practice"}.issubset(member_titles)
        assert client.get(f"/api/calendar/events/{squad_event_id}").status_code == 200
        _logout(client)

        _login(client, users["outsider"].username, passwords["outsider"])
        outsider_events = client.get("/api/calendar/events")
        assert outsider_events.status_code == 200
        outsider_titles = {row["title"] for row in outsider_events.json()}
        assert "Fleet-wide briefing" in outsider_titles
        assert "Black Tide drill" not in outsider_titles
        assert "Officer-led practice" not in outsider_titles
        assert client.get(f"/api/calendar/events/{squad_event_id}").status_code == 404
