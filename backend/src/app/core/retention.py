from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.configuration.models import MaintenanceSettings
from app.modules.accounts.models.registration_request import (
    REGISTRATION_PENDING,
    RegistrationRequest,
)
from app.modules.admin.models.audit_log import AuditLog
from app.modules.admin.models.ip_block import IpBlock
from app.modules.admin.models.outbound_webhook import OutboundWebhookDelivery
from app.modules.admin.models.security_event import SecuritySignalBucket
from app.modules.privacy.models.cookie_consent import CookieConsentDecision
from app.modules.privacy.models.data_subject_request import DataSubjectRequest


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

    security_cutoff_day = now.date() - timedelta(days=policy.security_event_retention_days - 1)
    inactive_block_cutoff = now - timedelta(days=policy.inactive_ip_block_retention_days)
    audit_log_cutoff = now - timedelta(days=policy.audit_log_retention_days)
    webhook_cutoff = now - timedelta(days=policy.webhook_delivery_retention_days)
    consent_cutoff = now - timedelta(days=policy.cookie_consent_retention_days)
    privacy_request_cutoff = now - timedelta(days=policy.resolved_privacy_request_retention_days)
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
    inactive_blocks = db.execute(
        delete(IpBlock).where(
            or_(
                IpBlock.unblocked_at < inactive_block_cutoff,
                (
                    IpBlock.unblocked_at.is_(None)
                    & IpBlock.expires_at.is_not(None)
                    & (IpBlock.expires_at < inactive_block_cutoff)
                ),
            )
        )
    )

    return {
        "security_signal_buckets": _delete_before(
            db, SecuritySignalBucket, SecuritySignalBucket.day, security_cutoff_day
        ),
        "inactive_ip_blocks": _deleted(inactive_blocks.rowcount),
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
        "resolved_privacy_requests": _deleted(
            db.execute(
                delete(DataSubjectRequest).where(
                    DataSubjectRequest.status != "pending",
                    DataSubjectRequest.resolved_at.is_not(None),
                    DataSubjectRequest.resolved_at < privacy_request_cutoff,
                )
            ).rowcount
        ),
        "registration_requests": _deleted(registration_result.rowcount),
    }
