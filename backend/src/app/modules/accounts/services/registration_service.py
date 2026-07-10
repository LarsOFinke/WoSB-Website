from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.modules.accounts.models.registration_request import RegistrationRequest
from app.modules.accounts.models.user import User
from app.modules.accounts.models.user_profile import UserProfile
from app.modules.accounts.models.registration_request import (
    REGISTRATION_APPROVED,
    REGISTRATION_PENDING,
    REGISTRATION_REJECTED,
    REGISTRATION_STATUSES,
)
from app.modules.accounts.models.user import ROLE_USER
from app.modules.accounts.schemas.register_request import RegisterRequest
from app.modules.admin.schemas.registration_decision import RegistrationDecision

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
    if len(payload.password) < 6:
        raise RegistrationRequestError("Password must contain at least 6 characters.")
    _assert_username_available(db, username)
    request = RegistrationRequest(
        username=username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip() or username,
        # Legacy fleet columns remain nullable for historical requests, but new
        # registrations can no longer create or request a membership.
        external_fleet_name=None,
        fleet_id=None,
        wants_fleet_membership=False,
        fleet_application_note=None,
        fleet_availability=None,
        fleet_preferred_ships=None,
        fleet_timezone=None,
        fleet_discord_handle=None,
        status=REGISTRATION_PENDING,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    logger.info("registration request submitted", extra={"path": "/api/auth/register"})
    return request


def list_registration_requests(db: Session, *, status: str | None = REGISTRATION_PENDING) -> list[RegistrationRequest]:
    query = select(RegistrationRequest).options(
        selectinload(RegistrationRequest.reviewed_by),
        selectinload(RegistrationRequest.created_user),
    )
    if status:
        if status not in REGISTRATION_STATUSES:
            raise RegistrationRequestError("Invalid registration status.")
        query = query.where(RegistrationRequest.status == status)
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
        role=ROLE_USER,
        is_active=True,
        profile=UserProfile(display_name=request.display_name),
    )
    db.add(user)
    db.flush()

    request.status = REGISTRATION_APPROVED
    request.decision_note = payload.note
    request.reviewed_by_id = reviewer.id
    request.reviewed_at = datetime.utcnow()
    request.created_user_id = user.id
    db.add(request)
    db.commit()
    db.refresh(request)
    logger.info("registration request approved", extra={"path": f"/api/admin/registration-requests/{request_id}/approve"})
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
    request.reviewed_at = datetime.utcnow()
    db.add(request)
    db.commit()
    db.refresh(request)
    logger.info("registration request rejected", extra={"path": f"/api/admin/registration-requests/{request_id}/reject"})
    return request
