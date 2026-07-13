from __future__ import annotations

import json
import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.admin.models.audit_log import AuditLog
from app.modules.admin.schemas.audit_log import AuditLogRead

logger = logging.getLogger(__name__)


def _date_bounds(from_date: date | None, to_date: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(from_date, time.min) if from_date else None
    end = datetime.combine(to_date + timedelta(days=1), time.min) if to_date else None
    return start, end


def record_audit(
    db: Session,
    *,
    actor: User,
    entity_type: str,
    entity_id: int | str,
    action: str,
    summary: str,
    changed_fields: list[str] | tuple[str, ...] | set[str] | None = None,
) -> AuditLog:
    fields = sorted({str(field) for field in (changed_fields or []) if str(field).strip()})
    row = AuditLog(
        actor_user_id=actor.id,
        actor_username=actor.username,
        actor_role=actor.role,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        summary=summary[:500],
        changed_fields_json=json.dumps(fields, ensure_ascii=False) if fields else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def record_audit_safely(db: Session, **kwargs) -> None:
    try:
        record_audit(db, **kwargs)
    except Exception:  # pragma: no cover - primary action must not be rolled back after its own commit
        db.rollback()
        logger.exception("audit log write failed", extra={"entity_type": kwargs.get("entity_type"), "entity_id": kwargs.get("entity_id")})


def list_audit_logs(
    db: Session,
    *,
    entity_type: str | None = None,
    action: str | None = None,
    actor: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 200,
) -> list[AuditLogRead]:
    query = select(AuditLog)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type.strip())
    if action:
        query = query.where(AuditLog.action == action.strip())
    if actor:
        query = query.where(AuditLog.actor_username.contains(actor.strip()))
    start, end = _date_bounds(from_date, to_date)
    if start:
        query = query.where(AuditLog.created_at >= start)
    if end:
        query = query.where(AuditLog.created_at < end)
    rows = db.scalars(query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)).all()
    result: list[AuditLogRead] = []
    for row in rows:
        try:
            changed_fields = json.loads(row.changed_fields_json or "[]")
        except json.JSONDecodeError:
            changed_fields = []
        result.append(
            AuditLogRead(
                id=row.id,
                created_at=row.created_at,
                actor_user_id=row.actor_user_id,
                actor_username=row.actor_username,
                actor_role=row.actor_role,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                action=row.action,
                summary=row.summary,
                changed_fields=changed_fields if isinstance(changed_fields, list) else [],
            )
        )
    return result
