from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from main import app


PUBLIC_READ_PATHS = (
    "/api/health",
    "/api/fleets",
    "/api/builds",
    "/api/builds/options",
    "/api/ships",
)

AUTHENTICATED_READ_PATHS = (
    "/api/guides",
    "/api/groups",
    "/api/forum/threads",
    "/api/calendar/events",
    "/api/fleets/manageable",
)


def test_public_and_authenticated_route_boundaries() -> None:
    with TestClient(app) as client:
        for path in PUBLIC_READ_PATHS:
            assert client.get(path).status_code == 200, path

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
