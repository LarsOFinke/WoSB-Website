from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.audit_log import AuditLogRead
from app.modules.admin.schemas.security_dashboard import SecurityDashboard
from app.modules.admin.services.audit_log_service import list_audit_logs
from app.modules.admin.services.security_dashboard_service import build_security_dashboard

router = APIRouter(tags=["admin-security"])


@router.get("/logs/security-dashboard", response_model=SecurityDashboard)
def admin_security_dashboard(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    threat_level: str | None = Query(
        default=None,
        pattern="^(low|guarded|elevated|critical)$",
    ),
    client_ip: str | None = Query(default=None, max_length=45),
    sort: str = Query(default="threat", pattern="^(threat|events|last_seen|ip)$"),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SecurityDashboard:
    """Return only aggregated IP-ban candidates; no raw request logs exist."""
    return build_security_dashboard(
        db,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        limit=limit,
        threat_level=threat_level,
        client_ip=client_ip,
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
