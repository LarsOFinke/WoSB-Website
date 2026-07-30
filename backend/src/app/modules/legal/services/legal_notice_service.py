from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.configuration.models import LegalNoticeSettings
from app.core.config import settings
from app.db.session import engine
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.legal.models.legal_notice import LegalNotice
from app.modules.legal.schemas.legal_notice import (
    LegalNoticeAdminRead,
    LegalNoticePublicRead,
    LegalNoticeUpdate,
)

LEGAL_NOTICE_ID = 1
LEGAL_NOTICE_FIELDS = tuple(asdict(settings.legal_notice).keys())


def _environment_values(config: LegalNoticeSettings | None = None) -> dict[str, object]:
    return asdict(config or settings.legal_notice)


def _row_or_create(db: Session) -> LegalNotice:
    row = db.get(LegalNotice, LEGAL_NOTICE_ID)
    if row is not None:
        return row
    row = LegalNotice(id=LEGAL_NOTICE_ID, **_environment_values())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ensure_legal_notice_from_environment() -> None:
    """Create or refresh the draft from .env until an administrator customizes it."""

    with Session(engine) as db:
        row = db.get(LegalNotice, LEGAL_NOTICE_ID)
        if row is None:
            db.add(LegalNotice(id=LEGAL_NOTICE_ID, **_environment_values()))
            db.commit()
            return
        if row.is_customized:
            return
        for field, value in _environment_values().items():
            setattr(row, field, value)
        row.updated_by_username = "environment"
        db.commit()


def serialize_admin(row: LegalNotice) -> LegalNoticeAdminRead:
    data = {field: getattr(row, field) for field in LEGAL_NOTICE_FIELDS}
    return LegalNoticeAdminRead(
        **data,
        source="admin" if row.is_customized else "environment",
        updated_by_username=row.updated_by_username,
        updated_at=row.updated_at,
    )


def get_admin_legal_notice(db: Session) -> LegalNoticeAdminRead:
    return serialize_admin(_row_or_create(db))


def get_public_legal_notice(db: Session) -> LegalNoticePublicRead:
    row = _row_or_create(db)
    if not row.published:
        return LegalNoticePublicRead(published=False, updated_at=row.updated_at)
    return LegalNoticePublicRead(
        **{field: getattr(row, field) for field in LEGAL_NOTICE_FIELDS},
        updated_at=row.updated_at,
    )


def update_legal_notice(
    db: Session,
    *,
    payload: LegalNoticeUpdate,
    actor: User,
) -> LegalNoticeAdminRead:
    row = _row_or_create(db)
    changed = []
    for field, value in payload.model_dump().items():
        if getattr(row, field) != value:
            setattr(row, field, value)
            changed.append(field)
    row.is_customized = True
    row.updated_by_username = actor.username
    db.commit()
    db.refresh(row)
    record_audit_safely(
        db,
        actor=actor,
        entity_type="legal_notice",
        entity_id=LEGAL_NOTICE_ID,
        action="update",
        summary="Legal notice settings updated.",
        changed_fields=changed or ["source"],
    )
    return serialize_admin(row)


def reset_legal_notice_to_environment(db: Session, *, actor: User) -> LegalNoticeAdminRead:
    row = _row_or_create(db)
    changed = []
    for field, value in _environment_values().items():
        if getattr(row, field) != value:
            setattr(row, field, value)
            changed.append(field)
    row.is_customized = False
    row.updated_by_username = "environment"
    db.commit()
    db.refresh(row)
    record_audit_safely(
        db,
        actor=actor,
        entity_type="legal_notice",
        entity_id=LEGAL_NOTICE_ID,
        action="restore",
        summary="Legal notice settings restored from environment configuration.",
        changed_fields=changed or ["source"],
    )
    return serialize_admin(row)
