from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.privacy.schemas.cookie_consent import (
    CookieConsentChoice,
    CookieConsentPolicy,
    CookieConsentRead,
)
from app.modules.privacy.services.cookie_consent_service import (
    COOKIE_CONSENT_COOKIE_NAME,
    COOKIE_CONSENT_MAX_AGE_SECONDS,
    COOKIE_POLICY_VERSION,
    consent_state,
    new_consent_key,
    record_decision,
    valid_consent_key,
)
from app.modules.privacy.schemas.data_subject_request import (
    DataSubjectRequestCreate,
    DataSubjectRequestRead,
)
from app.modules.privacy.services.data_export_service import PersonalDataExportService
from app.modules.privacy.services.data_subject_request_service import (
    DataSubjectRequestError,
    DataSubjectRequestService,
)

router = APIRouter(prefix="/privacy", tags=["privacy"])


def _request_read(request) -> DataSubjectRequestRead:
    return DataSubjectRequestRead(
        id=request.id,
        subject_user_id=request.subject_user_id,
        subject_username=request.subject.username,
        request_type=request.request_type,
        status=request.status,
        details=request.details,
        resolution_note=request.resolution_note,
        handled_by_user_id=request.handled_by_user_id,
        created_at=request.created_at,
        resolved_at=request.resolved_at,
    )


@router.get("/cookie-consent", response_model=CookieConsentRead)
def get_cookie_consent(
    consent_key: str | None = Cookie(default=None, alias=COOKIE_CONSENT_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> CookieConsentRead:
    return consent_state(db, consent_key)


@router.get("/cookie-policy", response_model=CookieConsentPolicy)
def get_cookie_policy() -> CookieConsentPolicy:
    return CookieConsentPolicy(version=COOKIE_POLICY_VERSION)


@router.post("/cookie-consent", response_model=CookieConsentRead)
def save_cookie_consent(
    payload: CookieConsentChoice,
    response: Response,
    consent_key: str | None = Cookie(default=None, alias=COOKIE_CONSENT_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> CookieConsentRead:
    key = valid_consent_key(consent_key) or new_consent_key()
    state = record_decision(db, consent_key=key, choice=payload, current_user=current_user)
    response.set_cookie(
        key=COOKIE_CONSENT_COOKIE_NAME,
        value=key,
        max_age=COOKIE_CONSENT_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return state


@router.get("/data-export")
def export_personal_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    return PersonalDataExportService(db).build(current_user)


@router.get("/requests", response_model=list[DataSubjectRequestRead])
def list_my_data_subject_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[DataSubjectRequestRead]:
    return [
        _request_read(request)
        for request in DataSubjectRequestService(db).list_for_user(current_user.id)
    ]


@router.post(
    "/requests",
    response_model=DataSubjectRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_data_subject_request(
    payload: DataSubjectRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> DataSubjectRequestRead:
    try:
        request = DataSubjectRequestService(db).create(current_user, payload)
    except DataSubjectRequestError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _request_read(request)
