from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_USER, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.privacy.models.data_subject_request import DataSubjectRequest
from app.modules.privacy.services.data_export_service import _RELATED_TABLES
from app.db.base import Base
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def test_personal_export_omits_authentication_secrets() -> None:
    username = "privacy-export-user"
    password = "PrivacyExportPassword123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Privacy Export",
                role=ROLE_USER,
            )
        _login(client, username, password)
        response = client.get("/api/privacy/data-export")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["subject"]["username"] == username
        serialized = response.text
        assert password not in serialized
        assert "password_hash" not in serialized
        assert "token_hash" not in serialized
        assert "consent_key" not in serialized


def test_personal_export_mapping_references_real_tables_and_columns() -> None:
    for table_name, owner_column in _RELATED_TABLES:
        table = Base.metadata.tables.get(table_name)
        assert table is not None, table_name
        assert owner_column in table.c, f"{table_name}.{owner_column}"


def test_deletion_request_requires_username_and_admin_pseudonymizes_account() -> None:
    username = "privacy-delete-user"
    password = "PrivacyDeletePassword123!"
    admin_username = "privacy-request-admin"
    admin_password = "PrivacyRequestAdmin123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="Delete Subject",
                role=ROLE_USER,
            )
            create_user(
                db,
                username=admin_username,
                password=admin_password,
                display_name="Privacy Admin",
                role=ROLE_ADMIN,
            )
        _login(client, username, password)
        rejected = client.post(
            "/api/privacy/requests",
            json={
                "request_type": "deletion",
                "details": "Please remove my account.",
                "confirmation": "wrong-user",
            },
        )
        assert rejected.status_code == 409
        created = client.post(
            "/api/privacy/requests",
            json={
                "request_type": "deletion",
                "details": "Please remove my account.",
                "confirmation": username,
            },
        )
        assert created.status_code == 201, created.text
        request_id = created.json()["id"]

        client.cookies.clear()
        _login(client, admin_username, admin_password)
        resolved = client.put(
            f"/api/admin/privacy-requests/{request_id}",
            json={"decision": "complete", "resolution_note": "Identity verified."},
        )
        assert resolved.status_code == 200, resolved.text
        assert resolved.json()["status"] == "completed"

    with SessionLocal() as db:
        subject = db.scalar(select(User).where(User.id == created.json()["subject_user_id"]))
        request = db.get(DataSubjectRequest, request_id)
        assert subject is not None
        assert subject.is_active is False
        assert subject.username.startswith(f"deleted-{subject.id}-")
        assert subject.profile is None
        assert request is not None and request.resolved_at is not None
