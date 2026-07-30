from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.legal.schemas.legal_notice import LegalNoticePublicRead
from app.modules.legal.services.legal_notice_service import get_public_legal_notice

router = APIRouter(prefix="/legal-notice", tags=["legal-notice"])


@router.get("", response_model=LegalNoticePublicRead)
def public_legal_notice(db: Session = Depends(get_db)) -> LegalNoticePublicRead:
    return get_public_legal_notice(db)
