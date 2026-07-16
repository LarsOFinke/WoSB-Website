from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import require_admin
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.system_update import (
    SystemUpdateRequest,
    SystemUpdateRequestResult,
    SystemUpdateStatus,
)
from app.modules.admin.services.system_update_service import (
    SystemUpdateError,
    get_system_update_status,
    request_system_update,
)

router = APIRouter(prefix="/system", tags=["admin-system"])


@router.get("/update", response_model=SystemUpdateStatus)
def admin_system_update_status(_: User = Depends(require_admin)) -> SystemUpdateStatus:
    return get_system_update_status()


@router.post(
    "/update",
    response_model=SystemUpdateRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
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
