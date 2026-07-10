from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff, require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.calendar.schemas.fleet_event_create import FleetEventCreate
from app.modules.calendar.schemas.fleet_event_read import FleetEventRead
from app.modules.calendar.schemas.fleet_event_update import FleetEventUpdate
from app.modules.calendar.services.fleet_event_service import (
    FleetEventValidationError,
    cancel_fleet_event,
    create_fleet_event,
    get_fleet_event,
    list_fleet_events,
    update_fleet_event,
)

router = APIRouter(prefix="/calendar/events", tags=["fleet calendar"])


@router.get("", response_model=list[FleetEventRead])
def get_events(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[FleetEventRead]:
    return list_fleet_events(db, start=start, end=end, category=category)


@router.post("", response_model=FleetEventRead, status_code=status.HTTP_201_CREATED)
def post_event(
    payload: FleetEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> FleetEventRead:
    try:
        return create_fleet_event(db, payload, current_user)
    except FleetEventValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{event_id}", response_model=FleetEventRead)
def get_event_detail(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> FleetEventRead:
    event = get_fleet_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return event


@router.put("/{event_id}", response_model=FleetEventRead)
def put_event(
    event_id: int,
    payload: FleetEventUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> FleetEventRead:
    try:
        event = update_fleet_event(db, event_id, payload)
    except FleetEventValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    if not cancel_fleet_event(db, event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
