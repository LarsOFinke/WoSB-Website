from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER
from app.modules.accounts.services.auth_service import create_user
from app.modules.onboarding.schemas.newcomer_guide import NewcomerGuideUpdate
from app.modules.onboarding.services.newcomer_guide_service import update_newcomer_guide
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def test_newcomer_guide_requires_login_and_staff_can_edit() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            admin = create_user(
                db,
                username="newcomer-admin",
                password="BlackwaterNewcomerAdmin123!",
                display_name="Newcomer Admin",
                role=ROLE_ADMIN,
            )
            create_user(
                db,
                username="newcomer-moderator",
                password="BlackwaterNewcomerModerator123!",
                display_name="Newcomer Moderator",
                role=ROLE_MODERATOR,
            )
            create_user(
                db,
                username="newcomer-member",
                password="BlackwaterNewcomerMember123!",
                display_name="Newcomer Member",
                role=ROLE_USER,
            )
            update_newcomer_guide(
                db,
                NewcomerGuideUpdate(
                    title="Test New Captain Guide",
                    intro="Start here.",
                    blocks=[
                        {
                            "block_type": "text",
                            "title": "First briefing",
                            "body": "Read, prepare, ask and join.",
                        },
                        {
                            "block_type": "resources",
                            "title": "Next links",
                            "resources": [
                                {
                                    "resource_type": "internal",
                                    "label": "Guides",
                                    "url": "/guides",
                                }
                            ],
                        },
                    ],
                ),
                admin,
            )

        assert client.get("/api/newcomer-guide").status_code == 401

        _login(client, "newcomer-member", "BlackwaterNewcomerMember123!")
        read = client.get("/api/newcomer-guide")
        assert read.status_code == 200
        assert read.json()["title"] == "Test New Captain Guide"
        assert read.json()["blocks"][1]["resources"][0]["href"] == "/guides"
        assert client.put(
            "/api/newcomer-guide",
            json={"title": "Denied", "intro": "", "blocks": []},
        ).status_code == 403
        assert client.post("/api/auth/logout").status_code == 204

        _login(client, "newcomer-moderator", "BlackwaterNewcomerModerator123!")
        updated = client.put(
            "/api/newcomer-guide",
            json={
                "title": "Moderator roadmap",
                "intro": "Curated by staff.",
                "blocks": [
                    {
                        "block_type": "text",
                        "title": "Added text field",
                        "body": "Staff can add optional text sections.",
                        "resources": [],
                    }
                ],
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["title"] == "Moderator roadmap"
        assert updated.json()["updated_by"] == "Newcomer Moderator"
