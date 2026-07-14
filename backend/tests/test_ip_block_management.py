from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.base import Base
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.schemas.ip_block import IpBlockCreate
from app.modules.admin.services.ip_block_service import (
    IpBlockError,
    create_ip_block,
    find_active_ip_block,
    ip_block_summary,
    list_ip_blocks,
    unblock_ip_block,
)
from app.modules.registry import register_all_models
from main import app


def isolated_session() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_ip_block_service_keeps_active_and_unblocked_history() -> None:
    with isolated_session() as db:
        actor = create_user(
            db,
            username="ip-block-service-moderator",
            password="BlackwaterIpBlock123!",
            display_name="IP Block Moderator",
            role=ROLE_MODERATOR,
        )
        row = create_ip_block(
            db,
            actor=actor,
            payload=IpBlockCreate(
                ip_address="2001:0db8:0:0:0:0:0:42",
                reason="Repeated vulnerability scans",
                expires_at=utc_now() + timedelta(hours=24),
            ),
        )
        assert row.ip_address == "2001:db8::42"
        assert row.is_active is True
        assert row.is_temporary is True
        assert find_active_ip_block(db, "2001:db8::42") is not None
        assert ip_block_summary(db).active == 1

        released = unblock_ip_block(db, block_id=row.id, actor=actor, reason="False positive")
        assert released.is_active is False
        assert released.unblock_reason == "False positive"
        assert find_active_ip_block(db, "2001:db8::42") is None
        assert len(list_ip_blocks(db, status="unblocked")) == 1
        summary = ip_block_summary(db)
        assert summary.active == 0
        assert summary.unblocked == 1


def test_ip_block_service_rejects_invalid_and_duplicate_active_addresses() -> None:
    with isolated_session() as db:
        actor = create_user(
            db,
            username="ip-block-validation-moderator",
            password="BlackwaterIpValidation123!",
            display_name="IP Validation Moderator",
            role=ROLE_MODERATOR,
        )
        for invalid in ("not-an-ip", "127.0.0.1", "::", "ff02::1"):
            try:
                create_ip_block(db, actor=actor, payload=IpBlockCreate(ip_address=invalid, reason="Invalid test"))
            except IpBlockError:
                pass
            else:  # pragma: no cover
                raise AssertionError(f"Expected {invalid} to be rejected")

        payload = IpBlockCreate(ip_address="198.51.100.77", reason="Scanner")
        create_ip_block(db, actor=actor, payload=payload)
        try:
            create_ip_block(db, actor=actor, payload=payload)
        except IpBlockError as exc:
            assert "already blocked" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected duplicate active IP block to be rejected")


def test_staff_can_block_and_unblock_ip_through_middleware() -> None:
    username = "ip-block-route-moderator"
    password = "BlackwaterIpRoute123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="IP Route Moderator",
                role=ROLE_ADMIN,
            )

        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200, login.text

        created = client.post(
            "/api/admin/ip-blocks",
            json={"ip_address": "203.0.113.91", "reason": "Automated exploit probes", "notes": "Regression test"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["is_active"] is True

        blocked = client.get("/api/builds", headers={"X-Forwarded-For": "203.0.113.91"})
        assert blocked.status_code == 403
        assert blocked.json()["code"] == "ip_blocked"
        assert blocked.headers["X-RBF-IP-Blocked"] == "1"

        spoof_attempt = client.get(
            "/api/builds",
            headers={"X-Real-IP": "203.0.113.91", "X-Forwarded-For": "198.51.100.1"},
        )
        assert spoof_attempt.status_code == 403

        health = client.get("/api/health", headers={"X-Forwarded-For": "203.0.113.91"})
        assert health.status_code == 200

        listing = client.get("/api/admin/ip-blocks", params={"status": "active"})
        assert listing.status_code == 200
        assert any(row["ip_address"] == "203.0.113.91" for row in listing.json())

        released = client.post(
            f"/api/admin/ip-blocks/{body['id']}/unblock",
            json={"reason": "Threat cleared"},
        )
        assert released.status_code == 200, released.text
        assert released.json()["is_active"] is False

        allowed_again = client.get("/api/builds", headers={"X-Forwarded-For": "203.0.113.91"})
        assert allowed_again.status_code != 403


def test_moderator_can_view_but_cannot_mutate_ip_blocks() -> None:
    username = "ip-block-readonly-moderator"
    password = "BlackwaterIpReadonly123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="IP Readonly Moderator",
                role=ROLE_MODERATOR,
            )
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200
        listing = client.get("/api/admin/ip-blocks")
        assert listing.status_code == 200
        denied = client.post(
            "/api/admin/ip-blocks",
            json={"ip_address": "203.0.113.199", "reason": "Moderator mutation check"},
        )
        assert denied.status_code == 403


def test_staff_cannot_block_current_request_ip() -> None:
    username = "ip-block-self-moderator"
    password = "BlackwaterIpSelf123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username=username,
                password=password,
                display_name="IP Self Moderator",
                role=ROLE_ADMIN,
            )
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200
        response = client.post(
            "/api/admin/ip-blocks",
            headers={"X-Forwarded-For": "198.51.100.123"},
            json={"ip_address": "198.51.100.123", "reason": "Would lock out current session"},
        )
        assert response.status_code == 400
        assert "current staff session" in response.text
