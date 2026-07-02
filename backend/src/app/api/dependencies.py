from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_access_token
from app.db.session import get_db
from app.models import User
from app.repositories import UserRepository

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def get_optional_current_user(db: DbSession, credentials: BearerCredentials) -> User | None:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None

    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        return None

    return UserRepository(db).get_by_id(user_id)


def get_current_user(db: DbSession, credentials: BearerCredentials) -> User:
    user = get_optional_current_user(db, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Anmeldung erforderlich.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]


def get_current_user_id(user: CurrentUser) -> int:
    return user.id


CurrentUserId = Annotated[int, Depends(get_current_user_id)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin-Rechte erforderlich.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
