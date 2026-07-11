from app.core.time import utc_now
import logging

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_session_token
from app.db.session import get_db
from app.modules.accounts.models.auth_session import AuthSession
from app.modules.accounts.models.user import User

logger = logging.getLogger(__name__)


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db),
) -> User | None:
    if not session_token:
        return None

    token_hash = hash_session_token(session_token)
    auth_session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))
    if auth_session is None:
        return None

    if auth_session.expires_at <= utc_now():
        db.execute(delete(AuthSession).where(AuthSession.id == auth_session.id))
        db.commit()
        logger.info("expired session removed", extra={"user_id": auth_session.user_id})
        return None

    if not auth_session.user.is_active:
        return None
    return auth_session.user


def require_user(current_user: User | None = Depends(get_current_user)) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required.")
    return current_user


def require_admin(current_user: User = Depends(require_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


def require_staff(current_user: User = Depends(require_user)) -> User:
    if not current_user.can_moderate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Moderator access required.")
    return current_user
