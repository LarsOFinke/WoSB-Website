from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FleetEvent, User
from app.schemas import FleetEventCreate, FleetEventRead, FleetEventUpdate


class FleetEventValidationError(ValueError):
    pass


def list_fleet_events(
    db: Session,
    start: datetime | None = None,
    end: datetime | None = None,
    category: str | None = None,
) -> list[FleetEventRead]:
    statement = select(FleetEvent).where(FleetEvent.is_cancelled.is_(False))
    if start is not None:
        statement = statement.where(FleetEvent.end_at >= start)
    if end is not None:
        statement = statement.where(FleetEvent.start_at <= end)
    if category:
        statement = statement.where(FleetEvent.category == category.strip().lower())
    statement = statement.order_by(FleetEvent.start_at.asc(), FleetEvent.id.asc())
    return [FleetEventRead.model_validate(event) for event in db.scalars(statement).unique().all()]


def get_fleet_event(db: Session, event_id: int) -> FleetEventRead | None:
    event = db.get(FleetEvent, event_id)
    if event is None or event.is_cancelled:
        return None
    return FleetEventRead.model_validate(event)


def create_fleet_event(db: Session, payload: FleetEventCreate, owner: User) -> FleetEventRead:
    event = FleetEvent(
        title=payload.title,
        category=payload.category,
        description=payload.description,
        location=payload.location,
        start_at=payload.start_at,
        end_at=payload.end_at,
        all_day=payload.all_day,
        owner_id=owner.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return FleetEventRead.model_validate(event)


def update_fleet_event(db: Session, event_id: int, payload: FleetEventUpdate) -> FleetEventRead | None:
    event = db.get(FleetEvent, event_id)
    if event is None or event.is_cancelled:
        return None
    for field_name, value in payload.model_dump().items():
        setattr(event, field_name, value)
    db.commit()
    db.refresh(event)
    return FleetEventRead.model_validate(event)


def cancel_fleet_event(db: Session, event_id: int) -> bool:
    event = db.get(FleetEvent, event_id)
    if event is None or event.is_cancelled:
        return False
    event.is_cancelled = True
    db.commit()
    return True
