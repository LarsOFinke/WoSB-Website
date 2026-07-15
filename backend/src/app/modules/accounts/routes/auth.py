from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.accounts.schemas.login_request import LoginRequest
from app.modules.accounts.schemas.login_response import LoginResponse
from app.modules.accounts.schemas.password_change_request import PasswordChangeRequest
from app.modules.accounts.schemas.password_change_response import PasswordChangeResponse
from app.modules.accounts.schemas.register_request import RegisterRequest
from app.modules.accounts.schemas.register_response import RegisterResponse
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.accounts.services.auth_service import (
    AuthError,
    authenticate_user,
    change_user_password,
    create_user_session,
    delete_session_by_token,
)
from app.modules.accounts.services.registration_service import RegistrationRequestError, submit_registration_request
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_hours * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.session_cookie_name, path="/")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_202_ACCEPTED)
def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    try:
        request = submit_registration_request(db, payload)
    except RegistrationRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    delivery_ids = queue_webhook_event_safely(
        db,
        event_type="registration.request.created",
        resource_type="registration_request",
        resource_id=request.id,
        resource_url="/admin?tab=registrations",
        actor=None,
        data={
            "id": request.id,
            "username": request.username,
            "display_name": request.display_name,
            "wants_fleet_membership": request.wants_fleet_membership,
            "fleet_id": request.fleet_id,
            "fleet_application_note": request.fleet_application_note,
        },
        **webhook_event_scope(db, fleet_id=request.fleet_id),
    )
    schedule_webhook_deliveries(background_tasks, delivery_ids)
    return RegisterResponse(request=request)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    token = create_user_session(db, user)
    _set_session_cookie(response, token)
    return LoginResponse(user=UserRead.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db),
) -> None:
    delete_session_by_token(db, session_token)
    _clear_session_cookie(response)


@router.post("/change-password", response_model=PasswordChangeResponse)
def change_password(
    payload: PasswordChangeRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> PasswordChangeResponse:
    try:
        change_user_password(db, current_user, payload.current_password, payload.new_password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    # All prior sessions are revoked by change_user_password. Rotate the current
    # browser into a fresh session so the user is not unexpectedly logged out.
    token = create_user_session(db, current_user)
    _set_session_cookie(response, token)
    return PasswordChangeResponse(changed=True)


@router.get("/me", response_model=UserRead | None)
def me(current_user: User | None = Depends(get_current_user)) -> UserRead | None:
    if current_user is None:
        return None
    return UserRead.model_validate(current_user)
