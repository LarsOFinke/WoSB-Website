from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from main import app


PUBLIC_READ_PATHS = (
    "/api/health",
    "/api/fleets/public/official",
)

AUTHENTICATED_READ_PATHS = (
    "/api/home",
    "/api/fleets",
    "/api/builds",
    "/api/builds/options",
    "/api/ships",
    "/api/guides",
    "/api/groups",
    "/api/forum/threads",
    "/api/calendar/events",
    "/api/fleets/manageable",
    "/api/newcomer-guide",
)


def test_public_and_authenticated_route_boundaries() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            if db.query(Fleet).count() == 0:
                db.add(Fleet(
                    name="Royal Blackwater Fleet",
                    slug="royal-blackwater-fleet",
                    focus="mixed",
                    description="Public fleet overview",
                    standing_orders="New captains first.",
                    sort_order=10,
                ))
                db.commit()

        for path in PUBLIC_READ_PATHS:
            assert client.get(path).status_code == 200, path

        public_fleet = client.get("/api/fleets/public/official")
        assert public_fleet.status_code == 200
        payload = public_fleet.json()
        assert set(payload) == {
            "id",
            "name",
            "slug",
            "focus",
            "description",
            "standing_orders",
            "active_members_count",
            "leaders",
        }
        assert "pending_members_count" not in payload
        assert all(set(leader) == {"display_name", "role"} for leader in payload["leaders"])

        for path in AUTHENTICATED_READ_PATHS:
            assert client.get(path).status_code == 401, path
        assert client.get("/api/admin/users").status_code == 401

        with SessionLocal() as db:
            create_user(
                db,
                username="route-admin",
                password="BlackwaterRouteTest123!",
                display_name="Route Admin",
                role=ROLE_ADMIN,
            )

        login_response = client.post(
            "/api/auth/login",
            json={"username": "route-admin", "password": "BlackwaterRouteTest123!"},
        )
        assert login_response.status_code == 200

        for path in AUTHENTICATED_READ_PATHS:
            assert client.get(path).status_code == 200, path
        assert client.get("/api/admin/users").status_code == 200
