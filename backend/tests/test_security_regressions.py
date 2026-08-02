from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.core.config import BACKEND_ROOT
from app.core.middleware import (
    ClientIpResolver,
    RequestLogContextFactory,
)
from app.core.security import PASSWORD_ITERATIONS, PasswordHasher
from app.db.schema_health import (
    DatabaseSchemaMismatchError,
    expected_alembic_heads,
    verify_alembic_heads,
)
from app.db.session import SessionLocal
from app.modules.accounts.models.auth_session import AuthSession
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import authenticate_user, create_user
from app.modules.admin.services.outbound_webhook_delivery_service.transport import (
    WebhookTargetError,
    WebhookTransport,
)
from app.modules.admin.services.outbound_webhook_service import (
    OutboundWebhookError,
    _validate_endpoint_url,
)
from main import app
from starlette.requests import Request as StarletteRequest


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def test_password_change_revokes_other_sessions_and_rotates_current_session() -> None:
    username = "session-rotation-user"
    old_password = "BlackwaterSessionOld123!"
    new_password = "BlackwaterSessionNew123!"
    with TestClient(app) as first, TestClient(app) as second:
        with SessionLocal() as db:
            user = create_user(
                db,
                username=username,
                password=old_password,
                display_name="Session Rotation User",
                role=ROLE_ADMIN,
            )
            user_id = user.id

        _login(first, username, old_password)
        _login(second, username, old_password)
        old_first_cookie = first.cookies.get("rbf_hub_session")
        old_second_cookie = second.cookies.get("rbf_hub_session")
        assert old_first_cookie and old_second_cookie and old_first_cookie != old_second_cookie

        changed = first.post(
            "/api/auth/change-password",
            json={"current_password": old_password, "new_password": new_password},
        )
        assert changed.status_code == 200, changed.text
        assert first.cookies.get("rbf_hub_session") not in {old_first_cookie, old_second_cookie}
        assert first.get("/api/auth/me").json()["username"] == username
        assert second.get("/api/auth/me").json() is None

        with SessionLocal() as db:
            assert db.query(AuthSession).filter(AuthSession.user_id == user_id).count() == 1


def test_legacy_password_hash_is_upgraded_after_successful_login() -> None:
    password = "BlackwaterLegacyHash123!"
    legacy_hasher = PasswordHasher(iterations=260_000)
    with SessionLocal() as db:
        user = create_user(
            db,
            username="legacy-password-user",
            password=password,
            display_name="Legacy Password User",
        )
        user.password_hash = legacy_hasher.hash(password)
        db.commit()
        user_id = user.id

    with SessionLocal() as db:
        authenticated = authenticate_user(db, "legacy-password-user", password)
        assert authenticated is not None
        assert authenticated.password_hash.startswith(
            f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        )
        assert authenticated.id == user_id


def test_cookie_authenticated_cross_origin_mutation_and_untrusted_host_are_rejected() -> None:
    username = "csrf-guard-user"
    password = "BlackwaterCsrfGuard123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="CSRF Guard User",
            )
        _login(client, username, password)

        rejected = client.post(
            "/api/auth/logout",
            headers={"Origin": "https://attacker.example", "Sec-Fetch-Site": "cross-site"},
        )
        assert rejected.status_code == 403, rejected.text
        assert client.get("/api/auth/me").json()["username"] == username

        untrusted = client.get("/api/health", headers={"Host": "attacker.example"})
        assert untrusted.status_code == 400


def test_svg_and_mismatched_uploads_are_rejected_but_valid_png_is_accepted() -> None:
    username = "secure-upload-user"
    password = "BlackwaterSecureUpload123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Secure Upload User",
            )
        _login(client, username, password)

        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        rejected_svg = client.post(
            "/api/files",
            files={"file": ("attack.svg", BytesIO(svg), "image/svg+xml")},
        )
        assert rejected_svg.status_code == 400

        disguised = client.post(
            "/api/files",
            files={"file": ("attack.png", BytesIO(svg), "image/png")},
        )
        assert disguised.status_code == 400

        png = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89"
        )
        accepted = client.post(
            "/api/files",
            files={"file": ("pixel.png", BytesIO(png), "image/png")},
        )
        assert accepted.status_code == 201, accepted.text
        assert accepted.json()["mime_type"] == "image/png"
        private_file = accepted.json()
        private_content_path = private_file["public_url"]
        assert private_content_path == f"/api/files/{private_file['id']}/content"

        response = client.get(private_content_path)
        assert response.status_code == 200
        assert response.content.startswith(b"\x89PNG")
        assert response.headers["cache-control"] == "private, no-store"
        assert response.headers["x-content-type-options"] == "nosniff"

        private_legacy_path = f"/uploads/{private_file['relative_path']}"
        legacy_response = client.get(private_legacy_path)
        assert legacy_response.status_code == 200
        assert legacy_response.content == response.content

        public_upload = client.post(
            "/api/files?usage_context=guide",
            files={"file": ("guide-pixel.png", BytesIO(png), "image/png")},
        )
        assert public_upload.status_code == 201, public_upload.text
        public_file = public_upload.json()
        public_content_path = public_file["public_url"]
        public_legacy_path = f"/uploads/{public_file['relative_path']}"

        client.cookies.clear()
        assert client.get(private_content_path).status_code == 401
        assert client.get(private_legacy_path).status_code == 401
        assert client.get(public_content_path).status_code == 401
        assert client.get(public_legacy_path).status_code == 401

        _login(client, username, password)
        guide = client.post(
            "/api/guides",
            json={
                "title": "Published attachment guide",
                "category": "general",
                "summary": "Attachment publication regression",
                "body": "The attached image is now part of published content.",
                "file_ids": [public_file["id"]],
                "build_ids": [],
            },
        )
        assert guide.status_code == 201, guide.text
        guide_id = guide.json()["id"]
        client.cookies.clear()
        assert client.get(public_content_path).status_code == 200
        assert client.get(public_legacy_path).status_code == 200

        _login(client, username, password)
        assert client.delete(f"/api/guides/{guide_id}").status_code == 204
        client.cookies.clear()
        assert client.get(public_content_path).status_code == 404
        assert client.get(public_legacy_path).status_code == 404

        _login(client, username, password)
        forum_upload = client.post(
            "/api/files?usage_context=forum",
            files={"file": ("forum-pixel.png", BytesIO(png), "image/png")},
        )
        assert forum_upload.status_code == 201, forum_upload.text
        forum_file = forum_upload.json()
        forum_content_path = forum_file["public_url"]
        client.cookies.clear()
        assert client.get(forum_content_path).status_code == 401

        _login(client, username, password)
        thread = client.post(
            "/api/forum/threads",
            json={
                "title": "Published attachment thread",
                "category": "general",
                "body": "The attached image is now part of a forum thread.",
                "file_ids": [forum_file["id"]],
            },
        )
        assert thread.status_code == 201, thread.text
        thread_id = thread.json()["id"]
        client.cookies.clear()
        assert client.get(forum_content_path).status_code == 200

        _login(client, username, password)
        detached = client.put(
            f"/api/forum/threads/{thread_id}",
            json={
                "title": "Published attachment thread",
                "category": "general",
                "body": "The forum attachment has been removed.",
                "file_ids": [],
            },
        )
        assert detached.status_code == 200, detached.text
        client.cookies.clear()
        assert client.get(forum_content_path).status_code == 401

        with SessionLocal() as db:
            create_user(
                db,
                username="other-upload-user",
                password="BlackwaterOtherUpload123!",
                display_name="Other Upload User",
            )
        _login(client, "other-upload-user", "BlackwaterOtherUpload123!")
        assert client.get(private_content_path).status_code == 403
        assert client.get(private_legacy_path).status_code == 403


def test_webhook_targets_block_private_literals_and_private_dns_results() -> None:
    with pytest.raises(OutboundWebhookError, match="private or reserved"):
        _validate_endpoint_url("https://127.0.0.1/api/webhooks/1/token")
    with pytest.raises(OutboundWebhookError, match="public network host"):
        _validate_endpoint_url("https://localhost/api/webhooks/1/token")

    def private_resolver(*_args, **_kwargs):
        return [(2, 1, 6, "", ("10.10.10.10", 443))]

    transport = WebhookTransport(resolver=private_resolver)
    with pytest.raises(WebhookTargetError, match="non-public"):
        transport.send(
            Request(
                "https://hooks.example.test/events",
                data=b"{}",
                method="POST",
            )
        )


def test_client_ip_resolver_rejects_forwarded_chains_and_log_context_is_minimal() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-forwarded-for", b"203.0.113.5, 10.0.0.5")],
        "client": ("172.18.0.4", 12345),
        "server": ("api", 8000),
        "scheme": "http",
        "query_string": b"",
    }
    request = StarletteRequest(scope)
    assert ClientIpResolver().resolve(request) == "172.18.0.4"

    single_hop_scope = {
        **scope,
        "headers": [(b"x-forwarded-for", b"203.0.113.5")],
        "query_string": b"search=Captain+Nemo",
    }
    context = RequestLogContextFactory().create(
        StarletteRequest(single_hop_scope),
        request_id="request-1",
        status_code=200,
        duration_ms=12.5,
    )
    assert context == {
        "request_id": "request-1",
        "method": "GET",
        "status_code": 200,
        "duration_ms": 12.5,
    }


def test_schema_head_resolution_uses_explicit_config_in_installed_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RBF_ALEMBIC_CONFIG", str(BACKEND_ROOT / "alembic.ini"))

    heads = expected_alembic_heads(tmp_path / "site-packages")

    assert heads == frozenset({"0024_build_file_attachments"})


def test_schema_head_resolution_rejects_missing_explicit_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing-alembic.ini"
    monkeypatch.setenv("RBF_ALEMBIC_CONFIG", str(missing))

    with pytest.raises(RuntimeError, match="RBF_ALEMBIC_CONFIG points to a missing"):
        expected_alembic_heads(tmp_path / "site-packages")


def test_schema_readiness_rejects_database_without_current_alembic_head(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'stale.db'}")
    with engine.connect() as connection, pytest.raises(DatabaseSchemaMismatchError):
        verify_alembic_heads(connection)


def test_master_data_uploads_require_admin_and_are_public_only_after_authorization() -> None:
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
                username="master-data-upload-user",
                password="BlackwaterMasterUploadUser123!",
                display_name="Master Data Upload User",
            )
            create_user(
                db,
                username="master-data-upload-admin",
                password="BlackwaterMasterUploadAdmin123!",
                display_name="Master Data Upload Admin",
                role=ROLE_ADMIN,
            )

        _login(client, "master-data-upload-user", "BlackwaterMasterUploadUser123!")
        denied = client.post(
            "/api/files?usage_context=master-data",
            files={"file": ("catalog.png", BytesIO(png), "image/png")},
        )
        assert denied.status_code == 403, denied.text

        _login(client, "master-data-upload-admin", "BlackwaterMasterUploadAdmin123!")
        accepted = client.post(
            "/api/files?usage_context=master-data",
            files={"file": ("catalog.png", BytesIO(png), "image/png")},
        )
        assert accepted.status_code == 201, accepted.text
        file_url = accepted.json()["public_url"]

        client.cookies.clear()
        public_response = client.get(file_url)
        assert public_response.status_code == 200
        assert public_response.headers["cache-control"] == "public, max-age=3600"
