from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_session_token, hash_password, hash_session_token, verify_password
from app.models import AuthSession, User
from app.schemas.fleet import FleetJoinRequest
from app.services.fleet_service import FleetValidationError, join_fleet
from app.models.user import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER

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
    fleet_name: str | None = None,
    fleet_id: int | None = None,
) -> User:
    normalized_username = username.strip().lower()
    if not normalized_username:
        raise AuthError("Username is required.")
    if role not in VALID_ROLES:
        raise AuthError("Invalid role.")
    if len(password) < 6:
        raise AuthError("Password must contain at least 6 characters.")
    if db.scalar(select(User).where(User.username == normalized_username)) is not None:
        raise AuthError("Username already exists.")

    user = User(
        username=normalized_username,
        display_name=display_name.strip() or normalized_username,
        password_hash=hash_password(password),
        role=role,
        fleet_name=(fleet_name.strip() or None) if isinstance(fleet_name, str) else None,
        fleet_id=fleet_id,
    )
    db.add(user)
    db.flush()
    if fleet_id is not None:
        try:
            join_fleet(db, user, FleetJoinRequest(fleet_id=fleet_id, note="Registration claim"))
        except FleetValidationError as exc:
            db.rollback()
            raise AuthError(str(exc)) from exc
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
    return user


def create_user_session(db: Session, user: User) -> str:
    token = create_session_token()
    token_hash = hash_session_token(token)
    expires_at = datetime.utcnow() + timedelta(hours=settings.session_ttl_hours)
    db.add(AuthSession(token_hash=token_hash, user_id=user.id, expires_at=expires_at))
    db.commit()
    return token


def delete_session_by_token(db: Session, token: str | None) -> None:
    if not token:
        return
    db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_session_token(token)))
    db.commit()


def delete_expired_sessions(db: Session) -> None:
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= datetime.utcnow()))
    db.commit()

def change_user_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Current password is incorrect.")
    if len(new_password) < 6:
        raise AuthError("Password must contain at least 6 characters.")
    user.password_hash = hash_password(new_password)
    db.commit()

