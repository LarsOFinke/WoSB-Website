from fastapi.testclient import TestClient
from sqlalchemy import select
from uuid import uuid4

from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN
from app.modules.accounts.services.auth_service import create_user
from app.modules.privacy.models.privacy_contact_request import PrivacyContactRequest
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def test_public_privacy_contact_reaches_admin_inbox_without_webhook_content() -> None:
    suffix = uuid4().hex[:8]
    admin_username = f"privacy-contact-admin-{suffix}"
    admin_password = "PrivacyContactAdmin123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=admin_username,
                password=admin_password,
                display_name="Privacy Contact Admin",
                role=ROLE_ADMIN,
            )

        created = client.post(
            "/api/privacy/contact",
            json={
                "reply_email": f"Subject-{suffix}@example.org",
                "subject": "Access question",
                "message": "Please explain which profile fields are stored.",
                "website": "",
            },
        )
        assert created.status_code == 201, created.text
        request_id = created.json()["id"]

        _login(client, admin_username, admin_password)
        listing = client.get("/api/admin/privacy-requests/contacts")
        assert listing.status_code == 200, listing.text
        row = next(item for item in listing.json() if item["id"] == request_id)
        assert row["reply_email"] == f"subject-{suffix}@example.org"
        assert row["message"] == "Please explain which profile fields are stored."

        resolved = client.put(
            f"/api/admin/privacy-requests/contacts/{request_id}",
            json={"decision": "complete", "resolution_note": "Answered by email."},
        )
        assert resolved.status_code == 200, resolved.text
        assert resolved.json()["status"] == "completed"

    with SessionLocal() as db:
        request = db.scalar(
            select(PrivacyContactRequest).where(PrivacyContactRequest.id == request_id)
        )
        assert request is not None and request.resolved_at is not None


def test_privacy_contact_honeypot_and_admin_boundary() -> None:
    payload = {
        "reply_email": "privacy@example.org",
        "subject": "Deletion question",
        "message": "I need help understanding the deletion process.",
        "website": "spam.example",
    }
    with TestClient(app) as client:
        assert client.post("/api/privacy/contact", json=payload).status_code == 422
        assert client.get("/api/admin/privacy-requests/contacts").status_code in {401, 403}
