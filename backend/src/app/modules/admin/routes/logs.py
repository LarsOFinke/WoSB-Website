from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, false, func, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.models.app_log import AppLog
from app.modules.admin.schemas.app_log_delete_result import AppLogDeleteResult
from app.modules.admin.schemas.app_log_read import AppLogRead
from app.modules.admin.schemas.app_log_summary import AppLogSummary
from app.modules.admin.schemas.audit_log import AuditLogRead
from app.modules.admin.schemas.security_dashboard import SecurityDashboard
from app.modules.admin.services.audit_log_service import list_audit_logs, record_audit_safely
from app.modules.admin.services.ip_block_service import active_blocked_ip_addresses
from app.modules.admin.services.security_dashboard_service import (
    build_security_dashboard,
    security_ip_addresses_for_level,
)

router = APIRouter(tags=["admin-security"])


def _app_log_filters(
    *,
    level: str | None = None,
    path: str | None = None,
    client_ip: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    threat_level: str | None = None,
    include_blocked: bool = False,
    db: Session | None = None,
):
    filters = []
    if level:
        filters.append(AppLog.level == level.upper())
    if path:
        filters.append(AppLog.path.contains(path.strip()))
    if client_ip:
        filters.append(AppLog.client_ip.contains(client_ip.strip()))
    if from_date:
        filters.append(AppLog.created_at >= datetime.combine(from_date, time.min))
    if to_date:
        filters.append(AppLog.created_at < datetime.combine(to_date + timedelta(days=1), time.min))
    if threat_level:
        if db is None:
            raise RuntimeError("A database session is required for threat-level filtering.")
        matching_ips = security_ip_addresses_for_level(
            db,
            from_date=from_date,
            to_date=to_date,
            threat_level=threat_level,
            include_blocked=include_blocked,
        )
        filters.append(
            or_(AppLog.client_ip.in_(matching_ips), AppLog.client.in_(matching_ips))
            if matching_ips
            else false()
        )
    if not include_blocked:
        if db is None:
            raise RuntimeError("A database session is required to exclude active IP blocks.")
        blocked_ips = active_blocked_ip_addresses(db)
        if blocked_ips:
            filters.append(
                and_(
                    or_(AppLog.client_ip.is_(None), AppLog.client_ip.not_in(blocked_ips)),
                    or_(AppLog.client.is_(None), AppLog.client.not_in(blocked_ips)),
                )
            )
    return filters


@router.get("/logs", response_model=list[AppLogRead])
def admin_list_logs(
    level: str | None = Query(default=None, max_length=20),
    path: str | None = Query(default=None, max_length=120),
    client_ip: str | None = Query(default=None, max_length=120),
    threat_level: str | None = Query(
        default=None,
        pattern="^(low|guarded|elevated|critical)$",
    ),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    include_blocked: bool = Query(default=False),
    sort: str = Query(default="created_at", pattern="^(created_at|level|status|duration|ip)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=120, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AppLogRead]:
    query = select(AppLog).where(
        *_app_log_filters(
            level=level,
            path=path,
            client_ip=client_ip,
            from_date=from_date,
            to_date=to_date,
            threat_level=threat_level,
            include_blocked=include_blocked,
            db=db,
        )
    )
    sort_column = {
        "created_at": AppLog.created_at,
        "level": AppLog.level,
        "status": AppLog.status_code,
        "duration": AppLog.duration_ms,
        "ip": AppLog.client_ip,
    }[sort]
    direction = sort_column.asc() if order == "asc" else sort_column.desc()
    rows = db.scalars(query.order_by(direction, AppLog.id.desc()).limit(limit)).all()
    return [AppLogRead.model_validate(row) for row in rows]


@router.get("/logs/summary", response_model=AppLogSummary)
def admin_log_summary(
    level: str | None = Query(default=None, max_length=20),
    path: str | None = Query(default=None, max_length=120),
    client_ip: str | None = Query(default=None, max_length=120),
    threat_level: str | None = Query(
        default=None,
        pattern="^(low|guarded|elevated|critical)$",
    ),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    include_blocked: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AppLogSummary:
    filters = _app_log_filters(
        level=level,
        path=path,
        client_ip=client_ip,
        from_date=from_date,
        to_date=to_date,
        threat_level=threat_level,
        include_blocked=include_blocked,
        db=db,
    )
    def count(*extra) -> int:
        return int(db.scalar(select(func.count(AppLog.id)).where(*filters, *extra)) or 0)
    status_ranges = {
        "2xx": (200, 300),
        "3xx": (300, 400),
        "4xx": (400, 500),
        "5xx": (500, 600),
    }
    return AppLogSummary(
        total=count(),
        errors=count(AppLog.level.in_(["ERROR", "CRITICAL"])),
        warnings=count(AppLog.level == "WARNING"),
        slow_requests=count(AppLog.duration_ms >= 750),
        recent_status={
            bucket: count(AppLog.status_code >= lower, AppLog.status_code < upper)
            for bucket, (lower, upper) in status_ranges.items()
        },
    )


@router.get("/logs/security-dashboard", response_model=SecurityDashboard)
def admin_security_dashboard(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    threat_level: str | None = Query(
        default=None,
        pattern="^(low|guarded|elevated|critical)$",
    ),
    client_ip: str | None = Query(default=None, max_length=120),
    include_blocked: bool = Query(default=False),
    sort: str = Query(default="threat", pattern="^(threat|requests|last_seen|ip)$"),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SecurityDashboard:
    return build_security_dashboard(
        db,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        limit=limit,
        threat_level=threat_level,
        client_ip=client_ip,
        include_blocked=include_blocked,
    )


@router.delete("/logs", response_model=AppLogDeleteResult)
def admin_delete_filtered_logs(
    level: str | None = Query(default=None, max_length=20),
    path: str | None = Query(default=None, max_length=120),
    client_ip: str | None = Query(default=None, max_length=120),
    threat_level: str | None = Query(
        default=None,
        pattern="^(low|guarded|elevated|critical)$",
    ),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    include_blocked: bool = Query(default=False),
    confirm: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AppLogDeleteResult:
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation is required to delete system logs.",
        )
    filters = _app_log_filters(
        level=level,
        path=path,
        client_ip=client_ip,
        from_date=from_date,
        to_date=to_date,
        threat_level=threat_level,
        include_blocked=include_blocked,
        db=db,
    )
    result = db.execute(delete(AppLog).where(*filters))
    deleted_count = int(result.rowcount or 0)
    db.commit()
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="app_log",
        entity_id="filtered",
        action="delete",
        summary=f"Deleted {deleted_count} system log entries from the active filter scope.",
        changed_fields=["system_logs"],
    )
    return AppLogDeleteResult(deleted_count=deleted_count)


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_log_entry(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    row = db.get(AppLog, log_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System log entry not found.")
    db.delete(row)
    db.commit()
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="app_log",
        entity_id=log_id,
        action="delete",
        summary=f"Deleted system log entry #{log_id}.",
        changed_fields=["system_log"],
    )


@router.get("/audit-logs", response_model=list[AuditLogRead])
def admin_audit_logs(
    entity_type: str | None = Query(default=None, max_length=40),
    action: str | None = Query(default=None, max_length=24),
    actor: str | None = Query(default=None, max_length=80),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AuditLogRead]:
    return list_audit_logs(
        db,
        entity_type=entity_type,
        action=action,
        actor=actor,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
