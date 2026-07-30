from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.calendar.models.fleet_event import FleetEvent
from app.modules.calendar.schemas.fleet_event_create import FleetEventCreate
from app.modules.calendar.schemas.fleet_event_read import CalendarSquadRead, FleetEventRead
from app.modules.calendar.schemas.fleet_event_update import FleetEventUpdate
from app.modules.fleet.services.fleet_service import can_manage_fleet, get_primary_fleet
from app.modules.raid_helper.services.raid_helper_service import configure_event_links, serialize_event_links
from app.modules.squads.models.squad import Squad
from app.modules.squads.services.squad_service import (
    can_manage_squad,
    can_view_squad_event,
    get_squad_model,
    user_managed_squad_ids,
    user_squad_ids,
)


class FleetEventValidationError(ValueError):
    pass


class FleetEventPermissionError(PermissionError):
    pass


def _serialize_event(
    db: Session,
    event: FleetEvent,
    user: User,
    *,
    can_manage: bool | None = None,
) -> FleetEventRead:
    squad = None
    if event.squad is not None:
        squad = CalendarSquadRead(id=event.squad.id, name=event.squad.name, slug=event.squad.slug)
    manager = _can_manage_scope(db, user, event.squad_id) if can_manage is None else can_manage
    return FleetEventRead(
        id=event.id,
        title=event.title,
        category=event.category,
        description=event.description,
        location=event.location,
        start_at=event.start_at,
        end_at=event.end_at,
        all_day=event.all_day,
        owner_id=event.owner_id,
        owner=event.owner,
        squad_id=event.squad_id,
        squad=squad,
        scope_type="squad" if event.squad_id is not None else "fleet",
        scope_name=event.squad.name if event.squad is not None else "Fleet",
        can_manage=manager,
        is_cancelled=event.is_cancelled,
        raid_helper_enabled=getattr(event, "raid_helper_enabled", True),
        raid_helper_links=(
            serialize_event_links(list(getattr(event, "raid_helper_links", [])))
            if manager
            else []
        ),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _can_manage_scope(db: Session, user: User, squad_id: int | None) -> bool:
    if squad_id is None:
        return can_manage_fleet(db, user)
    squad = get_squad_model(db, squad_id)
    return squad is not None and squad.is_active and can_manage_squad(db, user, squad)


def _validate_scope(db: Session, user: User, squad_id: int | None) -> Squad | None:
    if squad_id is None:
        if not can_manage_fleet(db, user):
            raise FleetEventPermissionError("Fleet leadership access required for fleet-wide events.")
        return None
    squad = get_squad_model(db, squad_id)
    if squad is None or not squad.is_active:
        raise FleetEventValidationError("Squad not found or archived.")
    primary = get_primary_fleet(db)
    if primary is None or squad.fleet_id != primary.id:
        raise FleetEventValidationError("Squad does not belong to the official fleet.")
    if not can_manage_squad(db, user, squad):
        raise FleetEventPermissionError("Squad leadership access required for this event.")
    return squad


def list_fleet_events(
    db: Session,
    user: User,
    start: datetime | None = None,
    end: datetime | None = None,
    category: str | None = None,
    squad_id: int | None = None,
    fleet_only: bool = False,
) -> list[FleetEventRead]:
    manages_fleet = can_manage_fleet(db, user)
    statement = select(FleetEvent).where(FleetEvent.is_cancelled.is_(False))
    if not manages_fleet:
        visible_squad_ids = user_squad_ids(db, user)
        statement = statement.where(
            or_(
                FleetEvent.squad_id.is_(None),
                FleetEvent.squad_id.in_(visible_squad_ids or [-1]),
            )
        )
    if start is not None:
        statement = statement.where(FleetEvent.end_at >= start)
    if end is not None:
        statement = statement.where(FleetEvent.start_at <= end)
    if category:
        statement = statement.where(FleetEvent.category == category.strip().lower())
    if fleet_only:
        statement = statement.where(FleetEvent.squad_id.is_(None))
    elif squad_id is not None:
        statement = statement.where(FleetEvent.squad_id == squad_id)
    statement = statement.order_by(FleetEvent.start_at.asc(), FleetEvent.id.asc())
    events = db.scalars(statement).unique().all()
    managed_squad_ids = set() if manages_fleet else set(user_managed_squad_ids(db, user))
    return [
        _serialize_event(
            db,
            event,
            user,
            can_manage=manages_fleet or (
                event.squad_id is not None and event.squad_id in managed_squad_ids
            ),
        )
        for event in events
    ]


def get_fleet_event(db: Session, event_id: int, user: User) -> FleetEventRead | None:
    event = db.get(FleetEvent, event_id)
    if event is None or event.is_cancelled or not can_view_squad_event(db, user, event.squad_id):
        return None
    return _serialize_event(db, event, user)


def create_fleet_event(db: Session, payload: FleetEventCreate, owner: User) -> FleetEventRead:
    _validate_scope(db, owner, payload.squad_id)
    event = FleetEvent(
        title=payload.title,
        category=payload.category,
        description=payload.description,
        location=payload.location,
        start_at=payload.start_at,
        end_at=payload.end_at,
        all_day=payload.all_day,
        owner_id=owner.id,
        squad_id=payload.squad_id,
        raid_helper_enabled=payload.raid_helper_enabled,
    )
    db.add(event)
    try:
        db.flush()
        if payload.raid_helper_enabled:
            configure_event_links(db, event, payload.raid_helper_dispatches, owner)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(event)
    return _serialize_event(db, event, owner)


def update_fleet_event(
    db: Session,
    event_id: int,
    payload: FleetEventUpdate,
    user: User,
) -> FleetEventRead | None:
    event = db.get(FleetEvent, event_id)
    if event is None or event.is_cancelled:
        return None
    if not _can_manage_scope(db, user, event.squad_id):
        raise FleetEventPermissionError("Event management access required.")
    _validate_scope(db, user, payload.squad_id)
    values = payload.model_dump(exclude={"raid_helper_dispatches"})
    for field_name, value in values.items():
        setattr(event, field_name, value)
    try:
        configure_event_links(db, event, payload.raid_helper_dispatches if payload.raid_helper_enabled else [], user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(event)
    return _serialize_event(db, event, user)


def cancel_fleet_event(db: Session, event_id: int, user: User) -> bool:
    event = db.get(FleetEvent, event_id)
    if event is None or event.is_cancelled:
        return False
    if not _can_manage_scope(db, user, event.squad_id):
        raise FleetEventPermissionError("Event management access required.")
    event.is_cancelled = True
    db.commit()
    return True
