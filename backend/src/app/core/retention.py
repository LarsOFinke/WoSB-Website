from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.configuration.models import MaintenanceSettings
from app.modules.accounts.models.registration_request import (
    REGISTRATION_PENDING,
    RegistrationRequest,
)
from app.modules.admin.models.app_log import AppLog
from app.modules.admin.models.audit_log import AuditLog
from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery
from app.modules.privacy.models.cookie_consent import CookieConsentDecision


def _deleted(rowcount: int | None) -> int:
    return int(rowcount or 0)


def _delete_before(db: Session, model, column, cutoff) -> int:
    result = db.execute(delete(model).where(column < cutoff))
    return _deleted(result.rowcount)


def purge_expired_records(
    db: Session,
    *,
    now,
    policy: MaintenanceSettings,
) -> dict[str, int]:
    """Apply the centrally documented data-retention policy."""

    app_log_cutoff = now - timedelta(days=policy.app_log_retention_days)
    audit_log_cutoff = now - timedelta(days=policy.audit_log_retention_days)
    webhook_cutoff = now - timedelta(days=policy.webhook_delivery_retention_days)
    consent_cutoff = now - timedelta(days=policy.cookie_consent_retention_days)
    pending_cutoff = now - timedelta(days=policy.pending_registration_retention_days)
    reviewed_cutoff = now - timedelta(days=policy.reviewed_registration_retention_days)

    registration_result = db.execute(
        delete(RegistrationRequest).where(
            or_(
                (RegistrationRequest.status == REGISTRATION_PENDING)
                & (RegistrationRequest.created_at < pending_cutoff),
                (RegistrationRequest.status != REGISTRATION_PENDING)
                & RegistrationRequest.reviewed_at.is_not(None)
                & (RegistrationRequest.reviewed_at < reviewed_cutoff),
            )
        )
    )

    return {
        "app_logs": _delete_before(db, AppLog, AppLog.created_at, app_log_cutoff),
        "audit_logs": _delete_before(db, AuditLog, AuditLog.created_at, audit_log_cutoff),
        "webhook_deliveries": _delete_before(
            db,
            OutboundWebhookDelivery,
            OutboundWebhookDelivery.created_at,
            webhook_cutoff,
        ),
        "cookie_consents": _delete_before(
            db,
            CookieConsentDecision,
            CookieConsentDecision.created_at,
            consent_cutoff,
        ),
        "registration_requests": _deleted(registration_result.rowcount),
    }
