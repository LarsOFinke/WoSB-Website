from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope
from app.modules.fleet.schemas.fleet_role import FleetRoleCreate, FleetRoleRead, FleetRoleUpdate
from app.modules.fleet.services.fleet_role_service import (
    FleetRolePermissionError,
    FleetRoleValidationError,
    create_fleet_role,
    delete_fleet_role,
    list_fleet_roles,
    update_fleet_role,
)

router = APIRouter(prefix="/fleets", tags=["fleets"])


def _raise(exc: Exception) -> None:
    if isinstance(exc, FleetRolePermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{fleet_id}/roles", response_model=list[FleetRoleRead])
def get_fleet_roles(
    fleet_id: int,
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[FleetRoleRead]:
    del fleet_id
    return list_fleet_roles(db, include_inactive=include_inactive)


@router.post("/{fleet_id}/roles", response_model=FleetRoleRead, status_code=status.HTTP_201_CREATED)
def post_fleet_role(
    fleet_id: int,
    payload: FleetRoleCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetRoleRead:
    try:
        row = create_fleet_role(db, fleet_id, payload, current_user)
    except (FleetRolePermissionError, FleetRoleValidationError) as exc:
        _raise(exc)
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="fleet_role",
        entity_id=row.id,
        action="create",
        summary=f'Fleet role “{row.label}” created.',
        changed_fields=list(payload.model_fields_set),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="fleet.role.created", resource_type="fleet_role", resource_id=row.id,
        resource_url="/fleets", actor=current_user, data=row,
        **webhook_event_scope(db, fleet_id=fleet_id),
    ))
    return row


@router.put("/{fleet_id}/roles/{role_id}", response_model=FleetRoleRead)
def put_fleet_role(
    fleet_id: int,
    role_id: int,
    payload: FleetRoleUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetRoleRead:
    try:
        row = update_fleet_role(db, fleet_id, role_id, payload, current_user)
    except (FleetRolePermissionError, FleetRoleValidationError) as exc:
        _raise(exc)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet role not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="fleet_role",
        entity_id=row.id,
        action="update",
        summary=f'Fleet role “{row.label}” updated.',
        changed_fields=list(payload.model_fields_set),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="fleet.role.updated", resource_type="fleet_role", resource_id=row.id,
        resource_url="/fleets", actor=current_user, data=row,
        **webhook_event_scope(db, fleet_id=fleet_id),
    ))
    return row


@router.delete("/{fleet_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    fleet_id: int,
    role_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = next((row for row in list_fleet_roles(db, include_inactive=True) if row.id == role_id), None)
    try:
        deleted = delete_fleet_role(db, fleet_id, role_id, current_user)
    except (FleetRolePermissionError, FleetRoleValidationError) as exc:
        _raise(exc)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet role not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="fleet_role",
        entity_id=role_id,
        action="delete",
        summary=f"Fleet role #{role_id} deleted.",
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="fleet.role.removed", resource_type="fleet_role", resource_id=role_id,
        resource_url="/fleets", actor=current_user,
        data=existing or {"id": role_id, "code": "removed", "label": f"Role #{role_id}"},
        **webhook_event_scope(db, fleet_id=fleet_id),
    ))
