from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER
from app.modules.accounts.services.auth_service import create_user
from app.modules.builds.models.build import Build
from app.modules.guides.models.guide import Guide
from app.modules.ships.models.ship import Ship
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


def test_newcomer_guide_can_link_published_guides_and_builds() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            admin = create_user(
                db,
                username="newcomer-link-admin",
                password="BlackwaterNewcomerLinks123!",
                display_name="Link Admin",
                role=ROLE_ADMIN,
            )
            ship = Ship(
                name="Guide Link Test Ship",
                rate=5,
                ship_type="Test Ship",
                durability=1000,
                speed_knots=10,
                maneuverability=5,
                armor=2,
                hold_capacity=100,
                crew_capacity=50,
            )
            db.add(ship)
            db.flush()
            guide = Guide(
                title="Linked Captain Guide",
                category="general",
                summary="A published linked guide.",
                body="Guide body",
                owner_id=admin.id,
                is_published=True,
            )
            build = Build(
                build_name="Linked Captain Build",
                build_type="balanced",
                ship_id=ship.id,
                owner_id=admin.id,
            )
            db.add_all([guide, build])
            db.commit()
            guide_id = guide.id
            build_id = build.id

        _login(client, "newcomer-link-admin", "BlackwaterNewcomerLinks123!")
        response = client.put(
            "/api/newcomer-guide",
            json={
                "title": "Linked roadmap",
                "intro": "Use these resources.",
                "blocks": [
                    {
                        "block_type": "resources",
                        "title": "Recommended guides and builds",
                        "body": "Open the resources below.",
                        "resources": [
                            {"resource_type": "guide", "resource_id": guide_id},
                            {"resource_type": "build", "resource_id": build_id},
                        ],
                    }
                ],
            },
        )
        assert response.status_code == 200, response.text
        resources = response.json()["blocks"][0]["resources"]
        assert resources[0]["label"] == "Linked Captain Guide"
        assert resources[0]["href"] == f"/guides/{guide_id}"
        assert resources[1]["label"] == "Linked Captain Build"
        assert resources[1]["href"] == f"/builds/{build_id}"
        assert all(resource["available"] for resource in resources)
