from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.legal.schemas.legal_notice import LegalNoticeAdminRead, LegalNoticeUpdate
from app.modules.legal.services.legal_notice_service import (
    get_admin_legal_notice,
    reset_legal_notice_to_environment,
    update_legal_notice,
)

router = APIRouter(prefix="/legal-notice", tags=["admin-legal-notice"])


@router.get("", response_model=LegalNoticeAdminRead)
def admin_get_legal_notice(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> LegalNoticeAdminRead:
    return get_admin_legal_notice(db)


@router.put("", response_model=LegalNoticeAdminRead)
def admin_update_legal_notice(
    payload: LegalNoticeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> LegalNoticeAdminRead:
    return update_legal_notice(db, payload=payload, actor=current_user)


@router.post("/reset-environment", response_model=LegalNoticeAdminRead)
def admin_reset_legal_notice(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> LegalNoticeAdminRead:
    return reset_legal_notice_to_environment(db, actor=current_user)
