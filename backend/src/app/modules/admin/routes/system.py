from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.system_update import (
    SystemUpdateRequest,
    SystemUpdateRequestResult,
    SystemUpdateStatus,
)
from app.modules.admin.services.outbound_webhook_delivery_service import (
    schedule_webhook_deliveries,
)
from app.modules.admin.services.system_update_service import (
    SystemUpdateError,
    get_system_update_status,
    request_system_update,
)
from app.modules.admin.services.system_update_webhook_service import (
    queue_pending_system_update_result,
    queue_system_update_started,
)

router = APIRouter(prefix="/system", tags=["admin-system"])

# Declared here so repository invariants can verify one route publisher per event.
_SYSTEM_UPDATE_WEBHOOK_EVENTS = (
    "system.update.started",
    "system.update.result",
    "system.maintenance.started",
    "system.maintenance.ended",
)


@router.get("/update", response_model=SystemUpdateStatus)
def admin_system_update_status(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SystemUpdateStatus:
    delivery_ids = queue_pending_system_update_result(db)
    schedule_webhook_deliveries(background_tasks, delivery_ids)
    return get_system_update_status()


@router.post(
    "/update",
    response_model=SystemUpdateRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_request_system_update(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: SystemUpdateRequest | None = None,
) -> SystemUpdateRequestResult:
    operation = payload.operation if payload is not None else "update"
    try:
        update_status = request_system_update(current_user, operation)
    except SystemUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    queue_system_update_started(db, actor=current_user, background_tasks=background_tasks)
    return SystemUpdateRequestResult(accepted=True, status=update_status)
