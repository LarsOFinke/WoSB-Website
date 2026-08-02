from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_MODERATOR, ROLE_USER
from app.modules.accounts.services.auth_service import create_user
from app.modules.files.models.file_asset import StoredFile
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


def test_forum_replies_can_be_deleted_by_author_or_moderator_but_not_as_opening_post() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="forum-delete-owner",
                password="ForumDeleteOwner123!",
                display_name="Forum Delete Owner",
                role=ROLE_USER,
            )
            create_user(
                db,
                username="forum-delete-other",
                password="ForumDeleteOther123!",
                display_name="Forum Delete Other",
                role=ROLE_USER,
            )
            create_user(
                db,
                username="forum-delete-moderator",
                password="ForumDeleteModerator123!",
                display_name="Forum Delete Moderator",
                role=ROLE_MODERATOR,
            )

        _login(client, "forum-delete-owner", "ForumDeleteOwner123!")
        created = client.post(
            "/api/forum/threads",
            json={
                "title": "Deletable replies",
                "category": "general",
                "body": "Opening post remains tied to the thread",
                "file_ids": [],
            },
        )
        assert created.status_code == 201, created.text
        thread_id = created.json()["id"]
        opening_post_id = created.json()["posts"][0]["id"]

        first_reply = client.post(
            f"/api/forum/threads/{thread_id}/posts",
            json={"body": "Owner removable reply", "file_ids": []},
        )
        assert first_reply.status_code == 201, first_reply.text
        first_reply_id = first_reply.json()["id"]

        opening_denied = client.delete(f"/api/forum/posts/{opening_post_id}")
        assert opening_denied.status_code == 400
        assert "opening post" in opening_denied.json()["detail"].lower()
        _logout(client)

        _login(client, "forum-delete-other", "ForumDeleteOther123!")
        unauthorized = client.delete(f"/api/forum/posts/{first_reply_id}")
        assert unauthorized.status_code == 404
        _logout(client)

        _login(client, "forum-delete-owner", "ForumDeleteOwner123!")
        owner_deleted = client.delete(f"/api/forum/posts/{first_reply_id}")
        assert owner_deleted.status_code == 204, owner_deleted.text
        second_reply = client.post(
            f"/api/forum/threads/{thread_id}/posts",
            json={"body": "Moderator removable reply", "file_ids": []},
        )
        assert second_reply.status_code == 201, second_reply.text
        second_reply_id = second_reply.json()["id"]
        _logout(client)

        _login(client, "forum-delete-moderator", "ForumDeleteModerator123!")
        moderator_deleted = client.delete(f"/api/forum/posts/{second_reply_id}")
        assert moderator_deleted.status_code == 204, moderator_deleted.text

        detail = client.get(f"/api/forum/threads/{thread_id}")
        assert detail.status_code == 200, detail.text
        assert [post["id"] for post in detail.json()["posts"]] == [opening_post_id]


def test_content_deletion_removes_orphaned_files_but_preserves_shared_files() -> None:
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89"
    )
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="content-file-delete-owner",
                password="ContentFileDeleteOwner123!",
                display_name="Content File Delete Owner",
                role=ROLE_USER,
            )

        _login(client, "content-file-delete-owner", "ContentFileDeleteOwner123!")

        def upload(name: str, context: str) -> dict:
            response = client.post(
                f"/api/files?usage_context={context}",
                files={"file": (name, BytesIO(png), "image/png")},
            )
            assert response.status_code == 201, response.text
            return response.json()

        guide_only = upload("guide-only.png", "guide")
        shared = upload("shared.png", "guide")
        forum_only = upload("forum-only.png", "forum")
        upload_root = Path(settings.upload_dir)
        paths = {
            item["id"]: upload_root / item["relative_path"]
            for item in (guide_only, shared, forum_only)
        }

        thread = client.post(
            "/api/forum/threads",
            json={
                "title": "Shared attachment thread",
                "category": "general",
                "body": "The shared attachment remains in use.",
                "file_ids": [shared["id"]],
            },
        )
        assert thread.status_code == 201, thread.text
        thread_id = thread.json()["id"]

        guide = client.post(
            "/api/guides",
            json={
                "title": "Guide file cleanup",
                "category": "general",
                "summary": "Deletion cleanup regression",
                "body": "One private and one shared attachment.",
                "file_ids": [guide_only["id"], shared["id"]],
                "build_ids": [],
            },
        )
        assert guide.status_code == 201, guide.text
        assert client.delete(f"/api/guides/{guide.json()['id']}").status_code == 204

        with SessionLocal() as db:
            assert db.get(StoredFile, guide_only["id"]) is None
            assert db.get(StoredFile, shared["id"]) is not None
        assert not paths[guide_only["id"]].exists()
        assert paths[shared["id"]].exists()

        reply = client.post(
            f"/api/forum/threads/{thread_id}/posts",
            json={"body": "Removable attachment", "file_ids": [forum_only["id"]]},
        )
        assert reply.status_code == 201, reply.text
        assert client.delete(f"/api/forum/posts/{reply.json()['id']}").status_code == 204

        with SessionLocal() as db:
            assert db.get(StoredFile, forum_only["id"]) is None
            assert db.get(StoredFile, shared["id"]) is not None
        assert not paths[forum_only["id"]].exists()
        assert paths[shared["id"]].exists()
