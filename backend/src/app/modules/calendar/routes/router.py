from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.outbound_webhook_delivery_service import queue_webhook_event_safely, schedule_webhook_deliveries
from app.modules.calendar.schemas.fleet_event_create import FleetEventCreate
from app.modules.calendar.schemas.fleet_event_read import FleetEventRead
from app.modules.calendar.schemas.fleet_event_update import FleetEventUpdate
from app.modules.calendar.services.fleet_event_service import (
    FleetEventPermissionError,
    FleetEventValidationError,
    cancel_fleet_event,
    create_fleet_event,
    get_fleet_event,
    list_fleet_events,
    update_fleet_event,
)

router = APIRouter(prefix="/calendar/events", tags=["fleet calendar"])


def _raise_event_error(exc: Exception) -> None:
    if isinstance(exc, FleetEventPermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[FleetEventRead])
def get_events(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    category: str | None = Query(default=None, max_length=80),
    squad_id: int | None = Query(default=None),
    fleet_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[FleetEventRead]:
    return list_fleet_events(
        db,
        current_user,
        start=start,
        end=end,
        category=category,
        squad_id=squad_id,
        fleet_only=fleet_only,
    )


@router.post("", response_model=FleetEventRead, status_code=status.HTTP_201_CREATED)
def post_event(
    payload: FleetEventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetEventRead:
    try:
        event = create_fleet_event(db, payload, current_user)
    except (FleetEventValidationError, FleetEventPermissionError) as exc:
        _raise_event_error(exc)
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="calendar.event.created", resource_type="calendar_event", resource_id=event.id,
        resource_url="/calendar", actor=current_user, data=event,
    ))
    return event


@router.get("/{event_id}", response_model=FleetEventRead)
def get_event_detail(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetEventRead:
    event = get_fleet_event(db, event_id, current_user)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return event


@router.put("/{event_id}", response_model=FleetEventRead)
def put_event(
    event_id: int,
    payload: FleetEventUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetEventRead:
    try:
        event = update_fleet_event(db, event_id, payload, current_user)
    except (FleetEventValidationError, FleetEventPermissionError) as exc:
        _raise_event_error(exc)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="calendar.event.updated", resource_type="calendar_event", resource_id=event.id,
        resource_url="/calendar", actor=current_user, data=event,
    ))
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = get_fleet_event(db, event_id, current_user)
    try:
        cancelled = cancel_fleet_event(db, event_id, current_user)
    except FleetEventPermissionError as exc:
        _raise_event_error(exc)
    if not cancelled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="calendar.event.cancelled", resource_type="calendar_event", resource_id=event_id,
        resource_url="/calendar", actor=current_user,
        data=existing or {"id": event_id, "is_cancelled": True},
    ))
