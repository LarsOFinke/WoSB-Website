from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.modules.privacy.models.cookie_consent import CookieConsentDecision
from app.modules.privacy.services.cookie_consent_service import COOKIE_POLICY_VERSION
from main import app


def test_anonymous_cookie_consent_is_persisted_append_only() -> None:
    with TestClient(app) as client:
        with SessionLocal() as db:
            db.execute(delete(CookieConsentDecision))
            db.commit()

        initial = client.get("/api/privacy/cookie-consent")
        assert initial.status_code == 200, initial.text
        assert initial.json() == {
            "necessary": True,
            "preferences": False,
            "analytics": False,
            "external_media": False,
            "has_decision": False,
            "policy_version": COOKIE_POLICY_VERSION,
            "decided_at": None,
        }

        accepted = client.post(
            "/api/privacy/cookie-consent",
            json={
                "necessary": True,
                "preferences": True,
                "analytics": False,
                "external_media": True,
            },
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["has_decision"] is True
        assert accepted.json()["preferences"] is True
        assert accepted.json()["external_media"] is True
        cookie_header = accepted.headers.get("set-cookie", "")
        assert "rbf_cookie_consent=" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=" in cookie_header

        loaded = client.get("/api/privacy/cookie-consent")
        assert loaded.status_code == 200, loaded.text
        assert loaded.json()["has_decision"] is True
        assert loaded.json()["preferences"] is True

        rejected = client.post(
            "/api/privacy/cookie-consent",
            json={
                "necessary": True,
                "preferences": False,
                "analytics": False,
                "external_media": False,
            },
        )
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["preferences"] is False
        assert rejected.json()["external_media"] is False

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(CookieConsentDecision)) == 2


def test_necessary_cookie_category_cannot_be_disabled() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/privacy/cookie-consent",
            json={
                "necessary": False,
                "preferences": False,
                "analytics": False,
                "external_media": False,
            },
        )
        assert response.status_code == 422


def test_invalid_consent_cookie_is_rotated_instead_of_stored() -> None:
    with TestClient(app) as client:
        client.cookies.set("rbf_cookie_consent", "invalid cookie value", domain="testserver.local", path="/")
        response = client.post(
            "/api/privacy/cookie-consent",
            json={
                "necessary": True,
                "preferences": False,
                "analytics": False,
                "external_media": False,
            },
        )
        assert response.status_code == 200, response.text
        rotated = client.cookies.get("rbf_cookie_consent", domain="testserver.local", path="/")
        assert rotated is not None
        assert rotated != "invalid cookie value"
        assert 32 <= len(rotated) <= 64


def test_cookie_policy_endpoint_exposes_current_version_and_categories() -> None:
    with TestClient(app) as client:
        response = client.get("/api/privacy/cookie-policy")
        assert response.status_code == 200, response.text
        assert response.json() == {
            "version": COOKIE_POLICY_VERSION,
            "categories": ["necessary", "preferences", "analytics", "external_media"],
        }
