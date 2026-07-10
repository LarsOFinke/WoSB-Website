from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from main import app


def test_authenticated_user_can_reply_to_forum_thread() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="forum-reply-admin",
                password="BlackwaterForumReply123!",
                display_name="Forum Reply Admin",
                role=ROLE_ADMIN,
            )

        login = client.post(
            "/api/auth/login",
            json={"username": "forum-reply-admin", "password": "BlackwaterForumReply123!"},
        )
        assert login.status_code == 200

        created = client.post(
            "/api/forum/threads",
            json={"title": "Reply regression", "category": "general", "body": "Initial post", "file_ids": []},
        )
        assert created.status_code == 201, created.text
        thread_id = created.json()["id"]

        reply = client.post(
            f"/api/forum/threads/{thread_id}/posts",
            json={"body": "This reply must persist without a NULL timestamp.", "file_ids": []},
        )
        assert reply.status_code == 201, reply.text
        payload = reply.json()
        assert payload["thread_id"] == thread_id
        assert payload["created_at"]
        assert payload["updated_at"]

        detail = client.get(f"/api/forum/threads/{thread_id}")
        assert detail.status_code == 200
        assert len(detail.json()["posts"]) == 2
