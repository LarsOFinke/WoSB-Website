from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db.session import SessionLocal
from app.modules.accounts.models.registration_request import (
    REDACTED_REGISTRATION_PASSWORD_HASH,
    RegistrationRequest,
)
from app.modules.accounts.models.user import ROLE_ADMIN, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.models.fleet_membership import FleetMembership
from main import app


ADMIN_USERNAME = "registration-fleet-admin"
ADMIN_PASSWORD = "RegistrationFleetAdmin123!"
MEMBER_USERNAME = "registration-fleet-user"
MEMBER_PASSWORD = "RegistrationFleetUser123!"
ACCOUNT_ONLY_USERNAME = "registration-account-only"


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def test_registration_can_optionally_create_a_pending_fleet_application() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            fleet = db.query(Fleet).order_by(Fleet.id).first()
            if fleet is None:
                fleet = Fleet(
                    name="Royal Blackwater Fleet",
                    slug="royal-blackwater-fleet",
                    focus="mixed",
                    description="Registration fleet fixture",
                    standing_orders="Account review first, fleet review second.",
                    sort_order=10,
                )
                db.add(fleet)
                db.commit()
                db.refresh(fleet)
            fleet_id = fleet.id
            initial_membership_count = db.query(FleetMembership).count()

            admin = db.query(User).filter(User.username == ADMIN_USERNAME).one_or_none()
            if admin is None:
                create_user(
                    db,
                    username=ADMIN_USERNAME,
                    password=ADMIN_PASSWORD,
                    display_name="Registration Fleet Admin",
                    role=ROLE_ADMIN,
                )

        inconsistent = client.post(
            "/api/auth/register",
            json={
                "username": "registration-inconsistent",
                "password": MEMBER_PASSWORD,
                "display_name": "Inconsistent Registration",
                "wants_fleet_membership": False,
                "fleet_application_note": "This must not be accepted without opting in.",
            },
        )
        assert inconsistent.status_code == 422, inconsistent.text

        wrong_fleet = client.post(
            "/api/auth/register",
            json={
                "username": "registration-wrong-fleet",
                "password": MEMBER_PASSWORD,
                "display_name": "Wrong Fleet",
                "wants_fleet_membership": True,
                "fleet_id": fleet_id + 100_000,
            },
        )
        assert wrong_fleet.status_code == 400, wrong_fleet.text

        account_only = client.post(
            "/api/auth/register",
            json={
                "username": ACCOUNT_ONLY_USERNAME,
                "password": MEMBER_PASSWORD,
                "display_name": "Account Only",
                "wants_fleet_membership": False,
                "fleet_id": None,
                "fleet_application_note": None,
            },
        )
        assert account_only.status_code == 202, account_only.text
        account_only_request_id = account_only.json()["request"]["id"]
        assert account_only.json()["request"]["wants_fleet_membership"] is False

        application_note = "Already an RBF member; please link this hub account."
        registration = client.post(
            "/api/auth/register",
            json={
                "username": MEMBER_USERNAME,
                "password": MEMBER_PASSWORD,
                "display_name": "Registration Fleet User",
                "wants_fleet_membership": True,
                "fleet_id": fleet_id,
                "fleet_application_note": application_note,
            },
        )
        assert registration.status_code == 202, registration.text
        request_payload = registration.json()["request"]
        request_id = request_payload["id"]
        assert request_payload["wants_fleet_membership"] is True
        assert request_payload["fleet_id"] == fleet_id
        assert request_payload["fleet_application_note"] == application_note

        with SessionLocal() as db:
            request = db.get(RegistrationRequest, request_id)
            assert request is not None
            registration_columns = {column["name"] for column in inspect(db.bind).get_columns("registration_requests")}
            assert {"fleet_id", "wants_fleet_membership", "fleet_application_note"}.issubset(registration_columns)
            assert {
                "external_fleet_name",
                "fleet_availability",
                "fleet_preferred_ships",
                "fleet_timezone",
                "fleet_discord_handle",
            }.isdisjoint(registration_columns)
            assert db.query(FleetMembership).count() == initial_membership_count

        _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
        pending_rows = client.get("/api/admin/registration-requests", params={"status": "pending"})
        assert pending_rows.status_code == 200, pending_rows.text
        row = next(item for item in pending_rows.json() if item["id"] == request_id)
        assert row["wants_fleet_membership"] is True
        assert row["fleet_id"] == fleet_id
        assert row["fleet_application_note"] == application_note

        account_only_approval = client.post(
            f"/api/admin/registration-requests/{account_only_request_id}/approve",
            json={"note": "Account approved without a fleet application."},
        )
        assert account_only_approval.status_code == 200, account_only_approval.text

        approval = client.post(
            f"/api/admin/registration-requests/{request_id}/approve",
            json={"note": "Account approved; fleet leadership will confirm membership."},
        )
        assert approval.status_code == 200, approval.text
        _logout(client)

        with SessionLocal() as db:
            account_only_user = db.query(User).filter(User.username == ACCOUNT_ONLY_USERNAME).one()
            assert db.query(FleetMembership).filter(FleetMembership.user_id == account_only_user.id).count() == 0

            reviewed_account_only = db.get(RegistrationRequest, account_only_request_id)
            reviewed_member = db.get(RegistrationRequest, request_id)
            assert reviewed_account_only.password_hash == REDACTED_REGISTRATION_PASSWORD_HASH
            assert reviewed_member.password_hash == REDACTED_REGISTRATION_PASSWORD_HASH

            member = db.query(User).filter(User.username == MEMBER_USERNAME).one()
            membership = db.query(FleetMembership).filter(FleetMembership.user_id == member.id).one()
            assert membership.fleet_id == fleet_id
            assert membership.status == "pending"
            assert membership.role == "member"
            assert membership.note == application_note

        _login(client, MEMBER_USERNAME, MEMBER_PASSWORD)
        memberships = client.get("/api/fleets/memberships/me")
        assert memberships.status_code == 200, memberships.text
        assert len(memberships.json()) == 1
        assert memberships.json()[0]["status"] == "pending"
        _logout(client)

        _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
        roster = client.get("/api/squads/roster")
        assert roster.status_code == 200, roster.text
        assert "Registration Fleet User" not in {row["display_name"] for row in roster.json()}
        _logout(client)
