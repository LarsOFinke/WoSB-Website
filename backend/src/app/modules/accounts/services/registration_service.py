from __future__ import annotations

from datetime import date, datetime, time, timedelta
import logging

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.password_policy import PasswordPolicyError, validate_password
from app.core.security import hash_password
from app.core.time import utc_now
from app.modules.accounts.models.registration_request import (
    REGISTRATION_APPROVED,
    REGISTRATION_PENDING,
    REGISTRATION_REJECTED,
    REGISTRATION_STATUSES,
    REDACTED_REGISTRATION_PASSWORD_HASH,
    RegistrationRequest,
)
from app.modules.accounts.models.user import ROLE_USER, User
from app.modules.accounts.models.user_profile import UserProfile
from app.modules.fleet.models.fleet import FLEET_MEMBER_PENDING, FLEET_ROLE_MEMBER, Fleet
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.services.fleet_service import get_primary_fleet
from app.modules.accounts.schemas.register_request import RegisterRequest
from app.modules.admin.schemas.registration_decision import RegistrationDecision
from app.modules.permissions.services.role_service import assign_fleet_role_definition, assign_site_role


logger = logging.getLogger("app.registration")


class RegistrationRequestError(ValueError):
    pass


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _assert_username_available(db: Session, username: str, *, excluding_request_id: int | None = None) -> None:
    if db.scalar(select(User.id).where(User.username == username)) is not None:
        raise RegistrationRequestError("Username already exists.")
    active_query = select(RegistrationRequest.id).where(
        RegistrationRequest.username == username,
        RegistrationRequest.status == REGISTRATION_PENDING,
    )
    if excluding_request_id is not None:
        active_query = active_query.where(RegistrationRequest.id != excluding_request_id)
    active_request = db.scalar(active_query)
    if active_request is not None:
        raise RegistrationRequestError("A registration request for this username is already waiting for review.")


def submit_registration_request(db: Session, payload: RegisterRequest) -> RegistrationRequest:
    username = _normalize_username(payload.username)
    try:
        validate_password(payload.password)
    except PasswordPolicyError as exc:
        raise RegistrationRequestError(str(exc)) from exc
    _assert_username_available(db, username)
    fleet: Fleet | None = None
    if payload.wants_fleet_membership:
        fleet = get_primary_fleet(db)
        if fleet is None or not fleet.is_active:
            raise RegistrationRequestError("Official fleet not found.")
        if payload.fleet_id is not None and payload.fleet_id != fleet.id:
            raise RegistrationRequestError("Only the official fleet can be joined.")

    request = RegistrationRequest(
        username=username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip() or username,
        wants_fleet_membership=payload.wants_fleet_membership,
        fleet_id=fleet.id if fleet is not None else None,
        fleet_application_note=payload.fleet_application_note if fleet is not None else None,
        status=REGISTRATION_PENDING,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    logger.info("registration request submitted")
    return request


def list_registration_requests(
    db: Session,
    *,
    status: str | None = REGISTRATION_PENDING,
    search: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[RegistrationRequest]:
    query = select(RegistrationRequest).options(
        selectinload(RegistrationRequest.reviewed_by),
        selectinload(RegistrationRequest.created_user),
    )
    if status:
        if status not in REGISTRATION_STATUSES:
            raise RegistrationRequestError("Invalid registration status.")
        query = query.where(RegistrationRequest.status == status)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(or_(
            RegistrationRequest.username.ilike(term),
            RegistrationRequest.display_name.ilike(term),
            RegistrationRequest.decision_note.ilike(term),
        ))
    if from_date:
        query = query.where(RegistrationRequest.created_at >= datetime.combine(from_date, time.min))
    if to_date:
        query = query.where(RegistrationRequest.created_at < datetime.combine(to_date + timedelta(days=1), time.min))
    return list(db.scalars(query.order_by(RegistrationRequest.created_at.desc(), RegistrationRequest.id.desc())).all())


def get_registration_request(db: Session, request_id: int) -> RegistrationRequest | None:
    return db.scalar(select(RegistrationRequest).where(RegistrationRequest.id == request_id))


def approve_registration_request(db: Session, request_id: int, reviewer: User, payload: RegistrationDecision) -> RegistrationRequest:
    request = get_registration_request(db, request_id)
    if request is None:
        raise RegistrationRequestError("Registration request not found.")
    if request.status != REGISTRATION_PENDING:
        raise RegistrationRequestError("Registration request is already reviewed.")
    _assert_username_available(db, request.username, excluding_request_id=request.id)

    user = User(
        username=request.username,
        password_hash=request.password_hash,
        is_active=True,
        profile=UserProfile(display_name=request.display_name),
    )
    assign_site_role(db, user, ROLE_USER)
    db.add(user)
    db.flush()

    if request.wants_fleet_membership:
        fleet = get_primary_fleet(db)
        if fleet is None or not fleet.is_active:
            raise RegistrationRequestError("Official fleet not found; fleet application cannot be created.")
        if request.fleet_id is not None and request.fleet_id != fleet.id:
            raise RegistrationRequestError("Requested fleet is no longer the official fleet.")
        membership = FleetMembership(
            fleet_id=fleet.id,
            user_id=user.id,
            status=FLEET_MEMBER_PENDING,
            note=request.fleet_application_note,
        )
        assign_fleet_role_definition(db, membership, FLEET_ROLE_MEMBER)
        db.add(membership)

    request.status = REGISTRATION_APPROVED
    request.decision_note = payload.note
    request.reviewed_by_id = reviewer.id
    request.reviewed_at = utc_now()
    request.created_user_id = user.id
    request.password_hash = REDACTED_REGISTRATION_PASSWORD_HASH
    db.add(request)
    db.commit()
    db.refresh(request)
    logger.info("registration request approved")
    return request


def reject_registration_request(db: Session, request_id: int, reviewer: User, payload: RegistrationDecision) -> RegistrationRequest:
    request = get_registration_request(db, request_id)
    if request is None:
        raise RegistrationRequestError("Registration request not found.")
    if request.status != REGISTRATION_PENDING:
        raise RegistrationRequestError("Registration request is already reviewed.")
    request.status = REGISTRATION_REJECTED
    request.decision_note = payload.note
    request.reviewed_by_id = reviewer.id
    request.reviewed_at = utc_now()
    request.password_hash = REDACTED_REGISTRATION_PASSWORD_HASH
    db.add(request)
    db.commit()
    db.refresh(request)
    logger.info("registration request rejected")
    return request
