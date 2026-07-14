from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, func, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_staff
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.models.app_log import AppLog
from app.modules.accounts.models.user import ROLE_MODERATOR
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.admin.schemas.app_log_read import AppLogRead
from app.modules.admin.schemas.app_log_summary import AppLogSummary
from app.modules.admin.schemas.audit_log import AuditLogRead
from app.modules.admin.schemas.security_dashboard import SecurityDashboard
from app.modules.admin.schemas.moderator_create import ModeratorCreate
from app.modules.admin.schemas.moderator_create_response import ModeratorCreateResponse
from app.modules.admin.schemas.registration_decision import RegistrationDecision
from app.modules.admin.schemas.registration_request_read import RegistrationRequestRead
from app.modules.admin.schemas.system_update import (
    SystemUpdateRequest,
    SystemUpdateRequestResult,
    SystemUpdateStatus,
)
from app.modules.admin.schemas.user_administration import UserAdministrationUpdate
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.forum.schemas.forum_thread_summary import ForumThreadSummary
from app.modules.guides.schemas.guide_summary import GuideSummary
from app.modules.accounts.services.auth_service import AuthError, create_user
from app.modules.builds.services.build_service import delete_build, get_build, list_builds
from app.modules.forum.services.forum_service import delete_thread, get_thread, list_threads
from app.modules.guides.services.guide_service import delete_guide, get_guide, list_guides
from app.modules.accounts.services.registration_service import RegistrationRequestError, approve_registration_request, list_registration_requests, reject_registration_request
from app.modules.admin.services.system_update_service import SystemUpdateError, get_system_update_status, request_system_update
from app.modules.admin.services.audit_log_service import list_audit_logs, record_audit_safely
from app.modules.admin.services.security_dashboard_service import build_security_dashboard, security_ip_addresses_for_level
from app.modules.admin.services.user_administration_service import UserAdministrationError, update_user_account
from app.modules.admin.routes.master_data import router as master_data_router

router = APIRouter(prefix="/admin", tags=["admin"])


def _app_log_filters(
    *,
    level: str | None = None,
    path: str | None = None,
    client_ip: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    threat_level: str | None = None,
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
        )
        if matching_ips:
            filters.append(or_(AppLog.client_ip.in_(matching_ips), AppLog.client.in_(matching_ips)))
        else:
            filters.append(false())
    return filters


@router.get("/system/update", response_model=SystemUpdateStatus)
def admin_system_update_status(
    _: User = Depends(require_staff),
) -> SystemUpdateStatus:
    return get_system_update_status()


@router.post("/system/update", response_model=SystemUpdateRequestResult, status_code=status.HTTP_202_ACCEPTED)
def admin_request_system_update(
    current_user: User = Depends(require_admin),
    payload: SystemUpdateRequest | None = None,
) -> SystemUpdateRequestResult:
    operation = payload.operation if payload is not None else "update"
    try:
        update_status = request_system_update(current_user, operation)
    except SystemUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return SystemUpdateRequestResult(accepted=True, status=update_status)

@router.get("/registration-requests", response_model=list[RegistrationRequestRead])
def admin_list_registration_requests(
    status_filter: str | None = Query(default="pending", alias="status", max_length=24),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[RegistrationRequestRead]:
    try:
        return [RegistrationRequestRead.model_validate(row) for row in list_registration_requests(db, status=status_filter)]
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/registration-requests/{request_id}/approve", response_model=RegistrationRequestRead)
def admin_approve_registration_request(
    request_id: int,
    payload: RegistrationDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> RegistrationRequestRead:
    try:
        request = approve_registration_request(db, request_id, current_user, payload)
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RegistrationRequestRead.model_validate(request)


@router.post("/registration-requests/{request_id}/reject", response_model=RegistrationRequestRead)
def admin_reject_registration_request(
    request_id: int,
    payload: RegistrationDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> RegistrationRequestRead:
    try:
        request = reject_registration_request(db, request_id, current_user, payload)
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RegistrationRequestRead.model_validate(request)


@router.get("/logs", response_model=list[AppLogRead])
def admin_list_logs(
    level: str | None = Query(default=None, max_length=20),
    path: str | None = Query(default=None, max_length=120),
    client_ip: str | None = Query(default=None, max_length=120),
    threat_level: str | None = Query(default=None, pattern="^(low|guarded|elevated|critical)$"),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    sort: str = Query(default="created_at", pattern="^(created_at|level|status|duration|ip)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=120, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[AppLogRead]:
    query = select(AppLog).where(*_app_log_filters(
        level=level,
        path=path,
        client_ip=client_ip,
        from_date=from_date,
        to_date=to_date,
        threat_level=threat_level,
        db=db,
    ))
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
    threat_level: str | None = Query(default=None, pattern="^(low|guarded|elevated|critical)$"),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> AppLogSummary:
    filters = _app_log_filters(
        level=level,
        path=path,
        client_ip=client_ip,
        from_date=from_date,
        to_date=to_date,
        threat_level=threat_level,
        db=db,
    )
    total = int(db.scalar(select(func.count(AppLog.id)).where(*filters)) or 0)
    errors = int(db.scalar(select(func.count(AppLog.id)).where(*filters, AppLog.level.in_(["ERROR", "CRITICAL"]))) or 0)
    warnings = int(db.scalar(select(func.count(AppLog.id)).where(*filters, AppLog.level == "WARNING")) or 0)
    slow_requests = int(db.scalar(select(func.count(AppLog.id)).where(*filters, AppLog.duration_ms >= 750)) or 0)
    status_ranges = {
        "2xx": (200, 300),
        "3xx": (300, 400),
        "4xx": (400, 500),
        "5xx": (500, 600),
    }
    recent_status = {
        bucket: int(
            db.scalar(
                select(func.count(AppLog.id)).where(
                    *filters, AppLog.status_code >= lower, AppLog.status_code < upper
                )
            )
            or 0
        )
        for bucket, (lower, upper) in status_ranges.items()
    }
    return AppLogSummary(
        total=total,
        errors=errors,
        warnings=warnings,
        slow_requests=slow_requests,
        recent_status=recent_status,
    )


@router.get("/logs/security-dashboard", response_model=SecurityDashboard)
def admin_security_dashboard(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    threat_level: str | None = Query(default=None, pattern="^(low|guarded|elevated|critical)$"),
    client_ip: str | None = Query(default=None, max_length=120),
    sort: str = Query(default="threat", pattern="^(threat|requests|last_seen|ip)$"),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> SecurityDashboard:
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
    _: User = Depends(require_staff),
) -> list[AuditLogRead]:
    return list_audit_logs(
        db, entity_type=entity_type, action=action, actor=actor,
        from_date=from_date, to_date=to_date, limit=limit,
    )


@router.get("/builds", response_model=list[BuildRead])
def admin_list_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[BuildRead]:
    return list_builds(db, search=search, build_type=build_type)


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    existing = get_build(db, build_id)
    deleted = delete_build(db, build_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="build", entity_id=build_id, action="delete",
        summary=f'Build “{getattr(existing, "build_name", build_id)}” removed by staff.',
    )


@router.get("/forum/threads", response_model=list[ForumThreadSummary])
def admin_list_forum_threads(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[ForumThreadSummary]:
    return list_threads(db, search=search, category=category)


@router.delete("/forum/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_forum_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    existing = get_thread(db, thread_id)
    if not delete_thread(db, thread_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum thread not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="forum_thread", entity_id=thread_id, action="delete",
        summary=f'Forum thread “{getattr(existing, "title", thread_id)}” removed by staff.',
    )


@router.get("/guides", response_model=list[GuideSummary])
def admin_list_guides(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[GuideSummary]:
    return list_guides(db, search=search, category=category)


@router.delete("/guides/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_guide(
    guide_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    existing = get_guide(db, guide_id)
    if not delete_guide(db, guide_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="guide", entity_id=guide_id, action="delete",
        summary=f'Guide “{getattr(existing, "title", guide_id)}” removed by staff.',
    )


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[UserRead]:
    users = db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all()
    return [UserRead.model_validate(user) for user in users]


@router.put("/users/{user_id}", response_model=UserRead)
def admin_update_user(
    user_id: int,
    payload: UserAdministrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> UserRead:
    try:
        user = update_user_account(db, actor=current_user, target_id=user_id, payload=payload)
    except UserAdministrationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return UserRead.model_validate(user)


@router.post("/moderators", response_model=ModeratorCreateResponse, status_code=status.HTTP_201_CREATED)
def admin_create_moderator(
    payload: ModeratorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ModeratorCreateResponse:
    try:
        user = create_user(
            db,
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            role=ROLE_MODERATOR,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ModeratorCreateResponse(user=UserRead.model_validate(user))


router.include_router(master_data_router)
