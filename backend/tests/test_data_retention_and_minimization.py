from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.configuration.models import MaintenanceSettings
from app.core.retention import purge_expired_records
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.models.registration_request import (
    REDACTED_REGISTRATION_PASSWORD_HASH,
    REGISTRATION_APPROVED,
    REGISTRATION_PENDING,
    RegistrationRequest,
)
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.accounts.schemas.user_reference_read import UserReferenceRead
from app.modules.admin.models.ip_block import IpBlock
from app.modules.admin.models.security_event import (
    SECURITY_SIGNAL_RECONNAISSANCE,
    SecuritySignalBucket,
)
from app.modules.admin.models.audit_log import AuditLog
from app.modules.admin.models.outbound_webhook import OutboundWebhook, OutboundWebhookDelivery
from app.modules.privacy.models.cookie_consent import CookieConsentDecision
from main import app


def _policy() -> MaintenanceSettings:
    return MaintenanceSettings(
        security_event_retention_days=7,
        inactive_ip_block_retention_days=90,
        audit_log_retention_days=365,
        webhook_delivery_retention_days=30,
        cookie_consent_retention_days=400,
        pending_registration_retention_days=30,
        reviewed_registration_retention_days=90,
        interval_hours=24,
    )


def test_retention_policy_removes_only_expired_operational_and_personal_records() -> None:
    now = utc_now()
    prefix = f"retention-{now.timestamp()}"
    with TestClient(app), SessionLocal() as db:
        webhook = OutboundWebhook(
            name=prefix,
            endpoint_url="https://discord.com/api/webhooks/123456789012345678/test-token",
            event_types_json='["integration.test"]',
            created_by_username="retention-test",
        )
        db.add(webhook)
        db.flush()

        old_log = SecuritySignalBucket(day=(now - timedelta(days=8)).date(), client_ip="198.51.100.30", signal=SECURITY_SIGNAL_RECONNAISSANCE, event_count=3)
        fresh_log = SecuritySignalBucket(day=(now - timedelta(days=1)).date(), client_ip="198.51.100.31", signal=SECURITY_SIGNAL_RECONNAISSANCE, event_count=2)
        inactive_block = IpBlock(
            ip_address="198.51.100.32", reason="expired", created_by_username=prefix,
            created_at=now - timedelta(days=120), expires_at=now - timedelta(days=91),
        )
        old_audit = AuditLog(
            created_at=now - timedelta(days=366), actor_username=prefix, actor_role="admin",
            entity_type="test", entity_id="old", action="delete", summary="old",
        )
        fresh_audit = AuditLog(
            created_at=now - timedelta(days=1), actor_username=prefix, actor_role="admin",
            entity_type="test", entity_id="fresh", action="update", summary="fresh",
        )
        old_delivery = OutboundWebhookDelivery(
            webhook_id=webhook.id, delivery_id=f"{prefix}-old", event_type="integration.test",
            resource_type="test", resource_id="old", payload_json="{}", status="delivered",
            created_at=now - timedelta(days=31),
        )
        fresh_delivery = OutboundWebhookDelivery(
            webhook_id=webhook.id, delivery_id=f"{prefix}-fresh", event_type="integration.test",
            resource_type="test", resource_id="fresh", payload_json="{}", status="delivered",
            created_at=now - timedelta(days=1),
        )
        old_consent = CookieConsentDecision(
            consent_key=f"{prefix}-old", policy_version="1", necessary=True,
            created_at=now - timedelta(days=401),
        )
        fresh_consent = CookieConsentDecision(
            consent_key=f"{prefix}-fresh", policy_version="1", necessary=True,
            created_at=now - timedelta(days=1),
        )
        old_pending = RegistrationRequest(
            username=f"{prefix}-pending", password_hash="old-hash", display_name="Old pending",
            status=REGISTRATION_PENDING, created_at=now - timedelta(days=31), updated_at=now,
        )
        fresh_pending = RegistrationRequest(
            username=f"{prefix}-fresh", password_hash="fresh-hash", display_name="Fresh pending",
            status=REGISTRATION_PENDING, created_at=now - timedelta(days=1), updated_at=now,
        )
        old_reviewed = RegistrationRequest(
            username=f"{prefix}-reviewed", password_hash=REDACTED_REGISTRATION_PASSWORD_HASH,
            display_name="Old reviewed", status=REGISTRATION_APPROVED,
            created_at=now - timedelta(days=100), reviewed_at=now - timedelta(days=91), updated_at=now,
        )
        db.add_all([
            old_log, fresh_log, inactive_block, old_audit, fresh_audit, old_delivery, fresh_delivery,
            old_consent, fresh_consent, old_pending, fresh_pending, old_reviewed,
        ])
        db.commit()
        ids = {
            "old_log": old_log.id, "fresh_log": fresh_log.id, "inactive_block": inactive_block.id,
            "old_audit": old_audit.id, "fresh_audit": fresh_audit.id,
            "old_delivery": old_delivery.id, "fresh_delivery": fresh_delivery.id,
            "old_consent": old_consent.id, "fresh_consent": fresh_consent.id,
            "old_pending": old_pending.id, "fresh_pending": fresh_pending.id,
            "old_reviewed": old_reviewed.id,
        }

        removed = purge_expired_records(db, now=now, policy=_policy())
        db.commit()

        assert removed == {
            "security_signal_buckets": 1,
            "inactive_ip_blocks": 1,
            "audit_logs": 1,
            "webhook_deliveries": 1,
            "cookie_consents": 1,
            "registration_requests": 2,
        }
        assert db.get(SecuritySignalBucket, ids["old_log"]) is None
        assert db.get(SecuritySignalBucket, ids["fresh_log"]) is not None
        assert db.get(IpBlock, ids["inactive_block"]) is None
        assert db.get(AuditLog, ids["old_audit"]) is None
        assert db.get(AuditLog, ids["fresh_audit"]) is not None
        assert db.get(OutboundWebhookDelivery, ids["old_delivery"]) is None
        assert db.get(OutboundWebhookDelivery, ids["fresh_delivery"]) is not None
        assert db.get(CookieConsentDecision, ids["old_consent"]) is None
        assert db.get(CookieConsentDecision, ids["fresh_consent"]) is not None
        assert db.get(RegistrationRequest, ids["old_pending"]) is None
        assert db.get(RegistrationRequest, ids["old_reviewed"]) is None
        assert db.get(RegistrationRequest, ids["fresh_pending"]) is not None

        db.delete(webhook)
        db.delete(fresh_log)
        db.delete(fresh_audit)
        db.delete(fresh_consent)
        db.delete(fresh_pending)
        db.commit()


def test_embedded_user_reference_exposes_only_the_minimum_identity() -> None:
    reference = UserReferenceRead.model_validate(
        SimpleNamespace(
            id=42,
            display_name="Quartermaster",
            username="private-login",
            role="admin",
            discord_handle="private#0001",
        )
    )
    assert reference.model_dump() == {"id": 42, "display_name": "Quartermaster"}


def test_user_read_collection_defaults_are_not_shared() -> None:
    base = dict(
        id=1,
        username="one",
        display_name="One",
        role="user",
        is_active=True,
        created_at=utc_now(),
    )
    first = UserRead(**base)
    second = UserRead(**{**base, "id": 2, "username": "two", "display_name": "Two"})
    first.preferred_ship_ids.append(7)
    assert second.preferred_ship_ids == []
