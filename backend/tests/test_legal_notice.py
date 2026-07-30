from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.accounts.models.user import ROLE_ADMIN, User
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.models.audit_log import AuditLog
from app.modules.legal.models.legal_notice import LegalNotice
from app.modules.registry import register_all_models
from main import app


ADMIN_USERNAME = "legal-notice-admin"
ADMIN_PASSWORD = "LegalNoticeAdmin123!"


def _reset_notice() -> None:
    register_all_models()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.execute(delete(LegalNotice))
        db.commit()


def _ensure_admin() -> None:
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == ADMIN_USERNAME)) is None:
            create_user(
                db,
                username=ADMIN_USERNAME,
                password=ADMIN_PASSWORD,
                display_name="Legal Notice Admin",
                role=ROLE_ADMIN,
            )


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text


def _published_payload() -> dict[str, object]:
    return {
        "published": True,
        "provider_name": "Example Community e.V.",
        "legal_form": "eingetragener Verein",
        "represented_by": "Board Example",
        "street": "Example Street 1",
        "postal_code": "12345",
        "city": "Example City",
        "country": "Deutschland",
        "email": "legal@example.invalid",
        "phone": "+49 123 456789",
        "register_name": "Vereinsregister",
        "register_court": "Amtsgericht Example City",
        "register_number": "VR 1234",
        "vat_id": "",
        "business_id": "",
        "supervisory_authority": "",
        "editorial_responsible_name": "Editorial Example",
        "editorial_responsible_street": "Example Street 1",
        "editorial_responsible_postal_code": "12345",
        "editorial_responsible_city": "Example City",
        "editorial_responsible_country": "Deutschland",
        "dispute_resolution_text": "No reviewed consumer dispute statement applies.",
        "additional_information": "Community project provider information.",
    }


def test_unpublished_legal_notice_does_not_expose_draft_provider_data() -> None:
    _reset_notice()
    with TestClient(app) as client:
        response = client.get("/api/legal-notice")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["published"] is False
        assert payload["provider_name"] == ""
        assert payload["email"] == ""
        assert "source" not in payload
        assert "updated_by_username" not in payload


def test_admin_can_publish_and_reset_legal_notice_while_regular_users_cannot() -> None:
    _reset_notice()
    _ensure_admin()
    regular_username = "legal-notice-member"
    regular_password = "LegalNoticeMember123!"
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == regular_username)) is None:
            create_user(
                db,
                username=regular_username,
                password=regular_password,
                display_name="Legal Notice Member",
            )

    with TestClient(app) as client:
        regular_login = client.post(
            "/api/auth/login",
            json={"username": regular_username, "password": regular_password},
        )
        assert regular_login.status_code == 200
        forbidden = client.get("/api/admin/legal-notice")
        assert forbidden.status_code == 403

        client.post("/api/auth/logout")
        _login(client)
        update = client.put("/api/admin/legal-notice", json=_published_payload())
        assert update.status_code == 200, update.text
        assert update.json()["source"] == "admin"
        assert update.json()["published"] is True

        public = client.get("/api/legal-notice")
        assert public.status_code == 200, public.text
        assert public.json()["provider_name"] == "Example Community e.V."
        assert public.json()["register_number"] == "VR 1234"
        assert "source" not in public.json()

        reset = client.post("/api/admin/legal-notice/reset-environment", json={})
        assert reset.status_code == 200, reset.text
        assert reset.json()["source"] == "environment"
        assert reset.json()["published"] is False

    with SessionLocal() as db:
        audit = db.scalar(
            select(AuditLog)
            .where(AuditLog.entity_type == "legal_notice")
            .order_by(AuditLog.id.desc())
        )
        assert audit is not None
        assert audit.action in {"update", "restore"}


def test_publishing_requires_complete_provider_details() -> None:
    _reset_notice()
    _ensure_admin()
    with TestClient(app) as client:
        _login(client)
        payload = _published_payload()
        payload["street"] = ""
        response = client.put("/api/admin/legal-notice", json=payload)
        assert response.status_code == 422, response.text
