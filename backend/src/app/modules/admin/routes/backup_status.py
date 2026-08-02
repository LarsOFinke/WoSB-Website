from fastapi import APIRouter, Depends

from app.core.dependencies import require_admin
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.backup_control import BackupControlStatus
from app.modules.admin.services.backup_control_service import (
    BackupControlService,
    get_backup_control_service,
)

router = APIRouter(prefix="/backups", tags=["admin-backups"])


@router.get("/status", response_model=BackupControlStatus)
def admin_backup_status(
    _: User = Depends(require_admin),
    service: BackupControlService = Depends(get_backup_control_service),
) -> BackupControlStatus:
    return service.get_status()
