from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.accounts.services.registration_service import (
    RegistrationRequestError,
    approve_registration_request,
    list_registration_requests,
    reject_registration_request,
)
from app.modules.admin.schemas.registration_decision import RegistrationDecision
from app.modules.admin.schemas.registration_request_read import RegistrationRequestRead
from app.modules.admin.services.audit_log_service import record_audit_safely

router = APIRouter(prefix="/registration-requests", tags=["admin-registrations"])


@router.get("", response_model=list[RegistrationRequestRead])
def admin_list_registration_requests(
    status_filter: str | None = Query(default="pending", alias="status", max_length=24),
    search: str | None = Query(default=None, max_length=120),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[RegistrationRequestRead]:
    try:
        return [
            RegistrationRequestRead.model_validate(row)
            for row in list_registration_requests(
                db,
                status=status_filter,
                search=search,
                from_date=from_date,
                to_date=to_date,
            )
        ]
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{request_id}/approve", response_model=RegistrationRequestRead)
def admin_approve_registration_request(
    request_id: int,
    payload: RegistrationDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> RegistrationRequestRead:
    try:
        request = approve_registration_request(db, request_id, current_user, payload)
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="registration_request",
        entity_id=request.id,
        action="update",
        summary=f'Access request for “{request.username}” approved.',
        changed_fields=[
            "status",
            "decision_note",
            "reviewed_by_id",
            "reviewed_at",
            "created_user_id",
            "fleet_membership",
        ],
    )
    return RegistrationRequestRead.model_validate(request)


@router.post("/{request_id}/reject", response_model=RegistrationRequestRead)
def admin_reject_registration_request(
    request_id: int,
    payload: RegistrationDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> RegistrationRequestRead:
    try:
        request = reject_registration_request(db, request_id, current_user, payload)
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="registration_request",
        entity_id=request.id,
        action="update",
        summary=f'Access request for “{request.username}” rejected.',
        changed_fields=["status", "decision_note", "reviewed_by_id", "reviewed_at"],
    )
    return RegistrationRequestRead.model_validate(request)
