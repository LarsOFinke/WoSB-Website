from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_session_token, hash_password, hash_session_token, verify_password
from app.modules.accounts.models.auth_session import AuthSession
from app.modules.accounts.models.registration_request import RegistrationRequest
from app.modules.accounts.models.user import User
from app.modules.accounts.models.user_profile import UserProfile
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
    if len(password) < 6:
        raise AuthError("Password must contain at least 6 characters.")
    if db.scalar(select(User).where(User.username == normalized_username)) is not None:
        raise AuthError("Username already exists.")
    if db.scalar(select(RegistrationRequest.id).where(RegistrationRequest.username == normalized_username, RegistrationRequest.status == REGISTRATION_PENDING)) is not None:
        raise AuthError("A registration request for this username is already waiting for review.")

    user = User(
        username=normalized_username,
        password_hash=hash_password(password),
        role=role,
        profile=UserProfile(display_name=display_name.strip() or normalized_username),
    )
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

