from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_bootstrap_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.backup_control import (
    BackupConfigurationRequest,
    BackupControlRequestResult,
    BackupControlStatus,
    BackupDiscoveryRequest,
    BackupEnrollmentResponseRequest,
    BackupOperation,
    DatabaseRestoreRequest,
)
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.backup_control_service import (
    BackupControlError,
    get_backup_control_status,
    request_backup_operation,
)

router = APIRouter(prefix="/backups", tags=["admin-backups"])


def _request(
    current_user: User,
    operation: BackupOperation,
    payload: dict | None = None,
) -> BackupControlRequestResult:
    try:
        backup_status = request_backup_operation(current_user, operation, payload)
    except BackupControlError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BackupControlRequestResult(accepted=True, status=backup_status)


@router.get("/status", response_model=BackupControlStatus)
def admin_backup_status(_: User = Depends(require_admin)) -> BackupControlStatus:
    return get_backup_control_status()


@router.post(
    "/key/prepare",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_prepare_backup_upload_key(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "prepare_key")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="upload_key",
        action="upload_key_prepared",
        summary="Dedicated SSH upload-key preparation requested.",
        changed_fields=["ssh_key"],
    )
    return result


@router.post(
    "/enrollment/prepare",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_prepare_backup_enrollment(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "prepare_enrollment")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="enrollment",
        action="enrollment_prepared",
        summary="Dedicated backup-server enrollment request creation requested.",
        changed_fields=["ssh_key"],
    )
    return result


@router.post(
    "/enrollment/apply",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_apply_backup_enrollment(
    payload: BackupEnrollmentResponseRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "apply_enrollment", payload.model_dump())
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="enrollment",
        action="enrollment_apply_requested",
        summary="Managed backup-server enrollment response import requested.",
        changed_fields=["connection", "host_key", "age_recipient"],
    )
    return result


@router.post(
    "/discover",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_discover_backup_host(
    payload: BackupDiscoveryRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "discover", payload.model_dump())
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="remote",
        action="discover_requested",
        summary=f"SSH host-key discovery requested for {payload.host}:{payload.port}.",
        changed_fields=["host", "port"],
    )
    return result


@router.put(
    "/configuration",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_configure_backup_host(
    payload: BackupConfigurationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "configure", payload.model_dump())
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="remote",
        action="configuration_requested",
        summary=(
            "Remote application backup connection update requested for "
            f"{payload.username}@{payload.host}:{payload.port}."
        ),
        changed_fields=["host", "port", "username", "remote_directory", "host_key", "private_key"],
    )
    return result


@router.delete(
    "/configuration",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_delete_backup_configuration(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "delete_configuration")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="remote",
        action="delete_requested",
        summary="Remote application backup connection removal requested.",
        changed_fields=["configuration", "private_key", "known_hosts"],
    )
    return result


@router.post(
    "/test",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_test_backup_connection(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "test")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="backup_connection",
        entity_id="remote",
        action="test_requested",
        summary="Remote application backup connection test requested.",
    )
    return result


@router.post(
    "/run",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_run_application_backup(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "backup")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="database_backup",
        entity_id="remote",
        action="backup_requested",
        summary="Database and uploaded-file backup creation and remote transfer requested.",
    )
    return result

@router.post(
    "/local/scan",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_scan_local_database_backups(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(current_user, "scan_local_backups")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="database_backup",
        entity_id="local_catalog",
        action="catalog_scan_requested",
        summary="Protected local PostgreSQL backup catalog refresh requested.",
    )
    return result


@router.post(
    "/local/restore",
    response_model=BackupControlRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_restore_local_database_backup(
    payload: DatabaseRestoreRequest,
    current_user: User = Depends(require_bootstrap_admin),
    db: Session = Depends(get_db),
) -> BackupControlRequestResult:
    result = _request(
        current_user,
        "restore_postgresql",
        {
            "backup_id": payload.backup_id,
            "approval_token_sha256": hashlib.sha256(
                payload.approval_token.get_secret_value().encode("utf-8")
            ).hexdigest(),
        },
    )
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="database_backup",
        entity_id=payload.backup_id[:16],
        action="restore_requested",
        summary="Bootstrap administrator requested a host-approved PostgreSQL restore.",
        changed_fields=["database"],
    )
    return result

