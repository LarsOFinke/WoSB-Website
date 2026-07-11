from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
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

router = APIRouter(prefix="/privacy", tags=["privacy"])


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
