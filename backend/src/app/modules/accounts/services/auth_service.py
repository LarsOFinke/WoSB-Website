from app.core.time import utc_now
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.password_policy import PasswordPolicyError, validate_password
from app.core.security import (
    create_session_token,
    hash_password,
    hash_session_token,
    password_hash_needs_rehash,
    verify_password,
)
from app.modules.accounts.models.auth_session import AuthSession
from app.modules.accounts.models.registration_request import RegistrationRequest
from app.modules.accounts.models.user import User
from app.modules.accounts.models.user_profile import UserProfile
from app.modules.permissions.services.role_service import assign_site_role
from app.modules.accounts.models.registration_request import REGISTRATION_PENDING
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER

VALID_ROLES = {ROLE_USER, ROLE_MODERATOR, ROLE_ADMIN}


class AuthError(ValueError):
    pass


def create_user(
    db: Session,
    *,
    username: str,
    password: str,
    display_name: str,
    role: str = ROLE_USER,
) -> User:
    normalized_username = username.strip().lower()
    if not normalized_username:
        raise AuthError("Username is required.")
    if role not in VALID_ROLES:
        raise AuthError("Invalid role.")
    try:
        validate_password(password)
    except PasswordPolicyError as exc:
        raise AuthError(str(exc)) from exc
    if db.scalar(select(User).where(User.username == normalized_username)) is not None:
        raise AuthError("Username already exists.")
    if db.scalar(select(RegistrationRequest.id).where(RegistrationRequest.username == normalized_username, RegistrationRequest.status == REGISTRATION_PENDING)) is not None:
        raise AuthError("A registration request for this username is already waiting for review.")

    user = User(
        username=normalized_username,
        password_hash=hash_password(password),
        profile=UserProfile(display_name=display_name.strip() or normalized_username),
    )
    assign_site_role(db, user, role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    normalized_username = username.strip().lower()
    user = db.scalar(select(User).where(User.username == normalized_username))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if password_hash_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
        db.refresh(user)
    return user


def create_user_session(db: Session, user: User) -> str:
    token = create_session_token()
    token_hash = hash_session_token(token)
    expires_at = utc_now() + timedelta(hours=settings.session_ttl_hours)
    db.add(AuthSession(token_hash=token_hash, user_id=user.id, expires_at=expires_at))
    db.commit()
    return token


def delete_session_by_token(db: Session, token: str | None) -> None:
    if not token:
        return
    db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_session_token(token)))
    db.commit()


def delete_expired_sessions(db: Session, *, commit: bool = True) -> int:
    result = db.execute(delete(AuthSession).where(AuthSession.expires_at <= utc_now()))
    if commit:
        db.commit()
    return int(result.rowcount or 0)


def revoke_user_sessions(db: Session, user_id: int, *, commit: bool = True) -> int:
    result = db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
    if commit:
        db.commit()
    return int(result.rowcount or 0)


def change_user_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Current password is incorrect.")
    try:
        validate_password(new_password)
    except PasswordPolicyError as exc:
        raise AuthError(str(exc)) from exc
    user.password_hash = hash_password(new_password)
    revoke_user_sessions(db, user.id, commit=False)
    db.commit()

