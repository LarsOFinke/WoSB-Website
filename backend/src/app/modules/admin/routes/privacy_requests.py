from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.privacy.routes.router import _request_read
from app.modules.privacy.schemas.data_subject_request import (
    DataSubjectRequestRead,
    DataSubjectRequestResolve,
)
from app.modules.privacy.services.data_subject_request_service import (
    DataSubjectRequestError,
    DataSubjectRequestService,
)

router = APIRouter(prefix="/privacy-requests", tags=["admin-privacy"])


@router.get("", response_model=list[DataSubjectRequestRead])
def list_privacy_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[DataSubjectRequestRead]:
    return [_request_read(row) for row in DataSubjectRequestService(db).list_all()]


@router.put("/{request_id}", response_model=DataSubjectRequestRead)
def resolve_privacy_request(
    request_id: int,
    payload: DataSubjectRequestResolve,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> DataSubjectRequestRead:
    try:
        request = DataSubjectRequestService(db).resolve(request_id, actor, payload)
    except DataSubjectRequestError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=actor,
        entity_type="privacy_request",
        entity_id=request.id,
        action=payload.decision,
        summary=f"Privacy {request.request_type} request resolved.",
        changed_fields=["status", "resolution_note"],
    )
    return _request_read(request)
