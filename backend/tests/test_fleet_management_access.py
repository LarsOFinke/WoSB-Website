from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_MODERATOR, ROLE_USER
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.services.fleet_service import assign_fleet_role
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204


def test_fleet_management_requires_staff_or_active_leadership_role() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            fleet = db.query(Fleet).order_by(Fleet.id).first()
            if fleet is None:
                fleet = Fleet(
                    name="Royal Blackwater Fleet",
                    slug="royal-blackwater-fleet",
                    focus="mixed",
                    description="Access policy fixture",
                    standing_orders="New captains first.",
                    sort_order=10,
                )
                db.add(fleet)
                db.commit()
                db.refresh(fleet)

            member = create_user(
                db,
                username="fleet-access-member",
                password="BlackwaterFleetMember123!",
                display_name="Fleet Member",
                role=ROLE_USER,
            )
            moderator = create_user(
                db,
                username="fleet-access-moderator",
                password="BlackwaterFleetModerator123!",
                display_name="Fleet Moderator",
                role=ROLE_MODERATOR,
            )
            lieutenant = create_user(
                db,
                username="fleet-access-lieutenant",
                password="BlackwaterFleetLieutenant123!",
                display_name="Fleet Lieutenant",
                role=ROLE_USER,
            )
            assign_fleet_role(db, fleet.id, lieutenant.id, "fleet_lieutenant")
            fleet_id = fleet.id

        _login(client, member.username, "BlackwaterFleetMember123!")
        assert client.get("/api/fleets/manageable").status_code == 403
        assert client.get(f"/api/fleets/{fleet_id}/manage").status_code == 403
        _logout(client)

        _login(client, moderator.username, "BlackwaterFleetModerator123!")
        assert client.get("/api/fleets/manageable").status_code == 200
        assert client.get(f"/api/fleets/{fleet_id}/manage").status_code == 200
        _logout(client)

        _login(client, lieutenant.username, "BlackwaterFleetLieutenant123!")
        assert client.get("/api/fleets/manageable").status_code == 200
        assert client.get(f"/api/fleets/{fleet_id}/manage").status_code == 200
