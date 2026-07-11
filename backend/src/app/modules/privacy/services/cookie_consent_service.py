from __future__ import annotations

import re
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.privacy.models.cookie_consent import CookieConsentDecision
from app.modules.privacy.schemas.cookie_consent import CookieConsentChoice, CookieConsentRead

COOKIE_CONSENT_COOKIE_NAME = "rbf_cookie_consent"
COOKIE_CONSENT_MAX_AGE_SECONDS = 365 * 24 * 60 * 60
COOKIE_POLICY_VERSION = "2026-07-11"
_CONSENT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,64}$")


def new_consent_key() -> str:
    return secrets.token_urlsafe(32)


def valid_consent_key(value: str | None) -> str | None:
    if not value or not _CONSENT_KEY_PATTERN.fullmatch(value):
        return None
    return value


def latest_decision(db: Session, consent_key: str | None) -> CookieConsentDecision | None:
    consent_key = valid_consent_key(consent_key)
    if not consent_key:
        return None
    return db.scalar(
        select(CookieConsentDecision)
        .where(CookieConsentDecision.consent_key == consent_key)
        .order_by(CookieConsentDecision.created_at.desc(), CookieConsentDecision.id.desc())
        .limit(1)
    )


def consent_state(db: Session, consent_key: str | None) -> CookieConsentRead:
    decision = latest_decision(db, consent_key)
    if decision is None or decision.policy_version != COOKIE_POLICY_VERSION:
        return CookieConsentRead(
            has_decision=False,
            policy_version=COOKIE_POLICY_VERSION,
            necessary=True,
            preferences=False,
            analytics=False,
            external_media=False,
            decided_at=None,
        )
    return CookieConsentRead(
        has_decision=True,
        policy_version=decision.policy_version,
        necessary=True,
        preferences=decision.preferences,
        analytics=decision.analytics,
        external_media=decision.external_media,
        decided_at=decision.created_at,
    )


def record_decision(
    db: Session,
    *,
    consent_key: str,
    choice: CookieConsentChoice,
    current_user: User | None,
) -> CookieConsentRead:
    decision = CookieConsentDecision(
        consent_key=consent_key,
        user_id=current_user.id if current_user else None,
        policy_version=COOKIE_POLICY_VERSION,
        necessary=True,
        preferences=choice.preferences,
        analytics=choice.analytics,
        external_media=choice.external_media,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return CookieConsentRead(
        has_decision=True,
        policy_version=decision.policy_version,
        necessary=True,
        preferences=decision.preferences,
        analytics=decision.analytics,
        external_media=decision.external_media,
        decided_at=decision.created_at,
    )
