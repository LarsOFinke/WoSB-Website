from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.guides.schemas.guide_create import GuideCreate
from app.modules.guides.schemas.guide_read import GuideRead
from app.modules.guides.schemas.guide_summary import GuideSummary
from app.modules.files.services.file_service import FileValidationError
from app.modules.guides.services.guide_service import GuideValidationError, create_guide, delete_guide, get_guide, list_guides

router = APIRouter(prefix="/guides", tags=["guides"])


@router.get("", response_model=list[GuideSummary])
def get_guides(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
) -> list[GuideSummary]:
    return list_guides(db, search=search, category=category)


@router.post("", response_model=GuideRead, status_code=status.HTTP_201_CREATED)
def post_guide(
    payload: GuideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> GuideRead:
    try:
        return create_guide(db, payload, current_user)
    except (FileValidationError, GuideValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{guide_id}", response_model=GuideRead)
def get_guide_detail(guide_id: int, db: Session = Depends(get_db)) -> GuideRead:
    guide = get_guide(db, guide_id)
    if guide is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    return guide


@router.delete("/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_guide(
    guide_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    if not delete_guide(db, guide_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
