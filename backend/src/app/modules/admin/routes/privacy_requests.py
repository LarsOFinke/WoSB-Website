from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.privacy.routes.router import _request_read
from app.modules.privacy.routes.router import _contact_read
from app.modules.privacy.schemas.data_subject_request import (
    DataSubjectRequestRead,
    DataSubjectRequestResolve,
)
from app.modules.privacy.services.data_subject_request_service import (
    DataSubjectRequestError,
    DataSubjectRequestService,
)
from app.modules.privacy.schemas.privacy_contact_request import (
    PrivacyContactRead,
    PrivacyContactResolve,
)
from app.modules.privacy.services.privacy_contact_service import (
    PrivacyContactError,
    PrivacyContactService,
)

router = APIRouter(prefix="/privacy-requests", tags=["admin-privacy"])


@router.get("/contacts", response_model=list[PrivacyContactRead])
def list_privacy_contacts(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[PrivacyContactRead]:
    return [_contact_read(row) for row in PrivacyContactService(db).list_all()]


@router.put("/contacts/{request_id}", response_model=PrivacyContactRead)
def resolve_privacy_contact(
    request_id: int,
    payload: PrivacyContactResolve,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> PrivacyContactRead:
    try:
        request = PrivacyContactService(db).resolve(request_id, actor, payload)
    except PrivacyContactError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=actor,
        entity_type="privacy_contact_request",
        entity_id=request.id,
        action=payload.decision,
        summary="Privacy contact request resolved.",
        changed_fields=["status", "resolution_note"],
    )
    return _contact_read(request)


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
    background_tasks: BackgroundTasks,
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
    delivery_ids = queue_webhook_event_safely(
        db,
        event_type="privacy.request.resolved",
        resource_type="privacy_request",
        resource_id=request.id,
        resource_url="/admin?tab=privacy-requests",
        actor=actor,
        data={
            "id": request.id,
            "request_type": request.request_type,
            "decision": payload.decision,
        },
        scope_type="global",
        scope_id=None,
        fleet_id=None,
        squad_id=None,
    )
    schedule_webhook_deliveries(background_tasks, delivery_ids)
    return _request_read(request)
