from __future__ import annotations

import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_bootstrap_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.routes.backup_route_support import notify_backup_restore, request_backup_operation
from app.modules.admin.schemas.backup_control import BackupControlRequestResult, FilesRestoreRequest
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.backup_control_service import BackupControlService, get_backup_control_service

router = APIRouter(prefix="/backups", tags=["admin-backups"])


@router.post(
    "/local/files/restore",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_restore_local_files_backup(
    payload: FilesRestoreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_bootstrap_admin),
    db: Session = Depends(get_db),
    service: BackupControlService = Depends(get_backup_control_service),
) -> BackupControlRequestResult:
    result = request_backup_operation(
        service,
        current_user,
        "restore_files",
        {
            "backup_id": payload.backup_id,
            "components": payload.components,
            "approval_token_sha256": hashlib.sha256(
                payload.approval_token.get_secret_value().encode("utf-8")
            ).hexdigest(),
        },
    )
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="files_backup",
        entity_id=payload.backup_id[:16],
        action="restore_requested",
        summary="Bootstrap administrator requested a host-approved modular file restore.",
        changed_fields=["components"],
    )
    notify_backup_restore(db, background_tasks, current_user, payload.backup_id)
    return result
