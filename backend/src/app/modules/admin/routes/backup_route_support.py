from __future__ import annotations

from fastapi import HTTPException, status

from app.modules.accounts.models.user import User
from app.modules.admin.schemas.backup_control import (
    BackupControlRequestResult,
    BackupOperation,
)
from app.modules.admin.services.backup_control_service import (
    BackupControlError,
    BackupControlService,
)


def request_backup_operation(
    service: BackupControlService,
    current_user: User,
    operation: BackupOperation,
    payload: dict | None = None,
) -> BackupControlRequestResult:
    try:
        backup_status = service.request_operation(current_user, operation, payload)
    except BackupControlError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BackupControlRequestResult(accepted=True, status=backup_status)
