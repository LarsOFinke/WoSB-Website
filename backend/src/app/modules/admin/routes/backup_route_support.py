from __future__ import annotations

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.admin.schemas.backup_control import (
    BackupControlRequestResult,
    BackupOperation,
)
from app.modules.admin.services.backup_control_service import (
    BackupControlError,
    BackupControlService,
)
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
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


def notify_backup_event(
    db: Session,
    background_tasks: BackgroundTasks,
    *,
    event_type: str,
    resource_type: str,
    resource_id: str,
    actor: User,
    data: dict | None = None,
) -> None:
    delivery_ids = queue_webhook_event_safely(
        db,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_url="/admin?tab=database-backups",
        actor=actor,
        data=data or {},
        scope_type="global",
        scope_id=None,
        fleet_id=None,
        squad_id=None,
    )
    schedule_webhook_deliveries(background_tasks, delivery_ids)


def notify_backup_configuration(
    db: Session, background_tasks: BackgroundTasks, actor: User, *, deleted: bool
) -> None:
    notify_backup_event(
        db,
        background_tasks,
        event_type=("backup.configuration.deleted" if deleted else "backup.configuration.updated"),
        resource_type="backup_connection",
        resource_id="remote",
        actor=actor,
        data={} if deleted else {"action": "updated"},
    )


def notify_backup_run(db: Session, background_tasks: BackgroundTasks, actor: User) -> None:
    notify_backup_event(
        db,
        background_tasks,
        event_type="backup.run.requested",
        resource_type="database_backup",
        resource_id="remote",
        actor=actor,
    )


def notify_backup_restore(
    db: Session, background_tasks: BackgroundTasks, actor: User, backup_id: str
) -> None:
    reference = backup_id[:16]
    notify_backup_event(
        db,
        background_tasks,
        event_type="backup.restore.requested",
        resource_type="database_backup",
        resource_id=reference,
        actor=actor,
        data={"backup_id": reference},
    )
