from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_MODERATOR, ROLE_USER
from app.modules.accounts.services.auth_service import create_user
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def test_guides_can_be_edited_by_owner_and_moderator() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="guide-edit-owner",
                password="GuideEditOwner123!",
                display_name="Guide Edit Owner",
                role=ROLE_USER,
            )
            create_user(
                db,
                username="guide-edit-other",
                password="GuideEditOther123!",
                display_name="Guide Edit Other",
                role=ROLE_USER,
            )
            create_user(
                db,
                username="guide-edit-moderator",
                password="GuideEditModerator123!",
                display_name="Guide Edit Moderator",
                role=ROLE_MODERATOR,
            )

        _login(client, "guide-edit-owner", "GuideEditOwner123!")
        created = client.post(
            "/api/guides",
            json={
                "title": "Markdown guide",
                "category": "general",
                "summary": "Initial summary",
                "body": "## Initial heading\n\n**Bold source**",
                "file_ids": [],
                "build_ids": [],
            },
        )
        assert created.status_code == 201, created.text
        guide_id = created.json()["id"]

        updated = client.put(
            f"/api/guides/{guide_id}",
            json={
                "title": "Edited Markdown guide",
                "category": "combat",
                "summary": "Updated summary",
                "body": "## Updated heading\n\n- one\n- two",
                "file_ids": [],
                "build_ids": [],
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["title"] == "Edited Markdown guide"
        assert updated.json()["body"] == "## Updated heading\n\n- one\n- two"
        _logout(client)

        _login(client, "guide-edit-other", "GuideEditOther123!")
        denied = client.put(
            f"/api/guides/{guide_id}",
            json={
                "title": "Denied",
                "category": "general",
                "summary": None,
                "body": "Denied edit",
                "file_ids": [],
                "build_ids": [],
            },
        )
        assert denied.status_code == 404
        _logout(client)

        _login(client, "guide-edit-moderator", "GuideEditModerator123!")
        moderated = client.put(
            f"/api/guides/{guide_id}",
            json={
                "title": "Moderated guide",
                "category": "combat",
                "summary": "Reviewed",
                "body": "> Reviewed by moderation",
                "file_ids": [],
                "build_ids": [],
            },
        )
        assert moderated.status_code == 200, moderated.text
        assert moderated.json()["body"] == "> Reviewed by moderation"


def test_forum_thread_and_reply_can_be_edited_with_permissions() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="forum-edit-owner",
                password="ForumEditOwner123!",
                display_name="Forum Edit Owner",
                role=ROLE_USER,
            )
            create_user(
                db,
                username="forum-edit-other",
                password="ForumEditOther123!",
                display_name="Forum Edit Other",
                role=ROLE_USER,
            )
            create_user(
                db,
                username="forum-edit-moderator",
                password="ForumEditModerator123!",
                display_name="Forum Edit Moderator",
                role=ROLE_MODERATOR,
            )

        _login(client, "forum-edit-owner", "ForumEditOwner123!")
        created = client.post(
            "/api/forum/threads",
            json={
                "title": "Editable thread",
                "category": "general",
                "body": "## Opening post",
                "file_ids": [],
            },
        )
        assert created.status_code == 201, created.text
        thread_id = created.json()["id"]

        reply = client.post(
            f"/api/forum/threads/{thread_id}/posts",
            json={"body": "Original reply", "file_ids": []},
        )
        assert reply.status_code == 201, reply.text
        reply_id = reply.json()["id"]

        thread_update = client.put(
            f"/api/forum/threads/{thread_id}",
            json={
                "title": "Edited thread",
                "category": "training",
                "body": "## Edited opening post\n\n1. First\n2. Second",
                "file_ids": [],
            },
        )
        assert thread_update.status_code == 200, thread_update.text
        assert thread_update.json()["title"] == "Edited thread"
        assert thread_update.json()["posts"][0]["body"].startswith("## Edited")

        reply_update = client.put(
            f"/api/forum/posts/{reply_id}",
            json={"body": "**Edited reply**", "file_ids": []},
        )
        assert reply_update.status_code == 200, reply_update.text
        assert reply_update.json()["body"] == "**Edited reply**"
        _logout(client)

        _login(client, "forum-edit-other", "ForumEditOther123!")
        denied = client.put(
            f"/api/forum/posts/{reply_id}",
            json={"body": "Denied", "file_ids": []},
        )
        assert denied.status_code == 404
        _logout(client)

        _login(client, "forum-edit-moderator", "ForumEditModerator123!")
        moderated = client.put(
            f"/api/forum/posts/{reply_id}",
            json={"body": "> Moderator edit", "file_ids": []},
        )
        assert moderated.status_code == 200, moderated.text
        assert moderated.json()["body"] == "> Moderator edit"
