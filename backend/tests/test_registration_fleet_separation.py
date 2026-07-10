from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.registration_request import RegistrationRequest
from app.modules.accounts.models.user import ROLE_ADMIN, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.models.fleet_membership import FleetMembership
from main import app


ADMIN_USERNAME = "registration-separation-admin"
ADMIN_PASSWORD = "RegistrationSeparationAdmin123!"
MEMBER_USERNAME = "registration-separation-user"
MEMBER_PASSWORD = "RegistrationSeparationUser123!"


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def test_registration_and_fleet_application_are_separate_workflows() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            fleet = db.query(Fleet).order_by(Fleet.id).first()
            if fleet is None:
                fleet = Fleet(
                    name="Royal Blackwater Fleet",
                    slug="royal-blackwater-fleet",
                    focus="mixed",
                    description="Registration separation fixture",
                    standing_orders="Accounts first, fleet applications second.",
                    sort_order=10,
                )
                db.add(fleet)
                db.commit()
                db.refresh(fleet)
            fleet_id = fleet.id

            admin = db.query(User).filter(User.username == ADMIN_USERNAME).one_or_none()
            if admin is None:
                create_user(
                    db,
                    username=ADMIN_USERNAME,
                    password=ADMIN_PASSWORD,
                    display_name="Registration Separation Admin",
                    role=ROLE_ADMIN,
                )

        legacy_payload = {
            "username": "legacy-registration-fleet-request",
            "password": MEMBER_PASSWORD,
            "display_name": "Legacy Fleet Request",
            "wants_fleet_membership": True,
            "fleet_id": fleet_id,
        }
        legacy_response = client.post("/api/auth/register", json=legacy_payload)
        assert legacy_response.status_code == 422, legacy_response.text

        registration = client.post(
            "/api/auth/register",
            json={
                "username": MEMBER_USERNAME,
                "password": MEMBER_PASSWORD,
                "display_name": "Registration Separation User",
            },
        )
        assert registration.status_code == 202, registration.text
        request_id = registration.json()["request"]["id"]

        with SessionLocal() as db:
            request = db.get(RegistrationRequest, request_id)
            assert request is not None
            assert request.fleet_id is None
            assert request.wants_fleet_membership is False
            assert request.fleet_application_note is None
            assert db.query(FleetMembership).filter(FleetMembership.user_id == request.created_user_id).count() == 0

        _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
        approval = client.post(
            f"/api/admin/registration-requests/{request_id}/approve",
            json={"note": "Account approved; fleet membership remains separate."},
        )
        assert approval.status_code == 200, approval.text
        _logout(client)

        with SessionLocal() as db:
            member = db.query(User).filter(User.username == MEMBER_USERNAME).one()
            member_id = member.id
            assert db.query(FleetMembership).filter(FleetMembership.user_id == member_id).count() == 0

        _login(client, MEMBER_USERNAME, MEMBER_PASSWORD)
        application = client.post(
            "/api/fleets/join",
            json={
                "fleet_id": fleet_id,
                "note": "Ready to apply after account approval.",
                "availability": "Evenings",
                "preferred_ships": "Line ships",
                "timezone": "CET",
                "discord_handle": "separation-test",
            },
        )
        assert application.status_code == 201, application.text
        assert application.json()["status"] == "pending"
        _logout(client)

        _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
        roster = client.get("/api/squads/roster")
        assert roster.status_code == 200, roster.text
        assert "Registration Separation User" not in {row["display_name"] for row in roster.json()}
        _logout(client)
