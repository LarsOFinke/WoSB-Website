from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff, require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.onboarding.schemas.newcomer_guide import NewcomerGuideRead, NewcomerGuideUpdate
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_service import queue_webhook_event_safely, schedule_webhook_deliveries
from app.modules.onboarding.services.newcomer_guide_service import (
    NewcomerGuideValidationError,
    get_newcomer_guide,
    update_newcomer_guide,
)

router = APIRouter(prefix="/newcomer-guide", tags=["newcomer-guide"])


@router.get("", response_model=NewcomerGuideRead)
def read_newcomer_guide(
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> NewcomerGuideRead:
    try:
        return get_newcomer_guide(db)
    except NewcomerGuideValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("", response_model=NewcomerGuideRead)
def replace_newcomer_guide(
    payload: NewcomerGuideUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> NewcomerGuideRead:
    try:
        guide = update_newcomer_guide(db, payload, current_user)
    except NewcomerGuideValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db, actor=current_user, entity_type="newcomer_guide", entity_id=guide.id, action="update",
        summary="Starter guide updated.",
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="newcomer_guide.updated", resource_type="newcomer_guide",
        resource_id=guide.id, resource_url="/newcomer-guide", actor=current_user, data=guide,
    ))
    return guide
