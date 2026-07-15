from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.guides.schemas.guide_create import GuideCreate
from app.modules.guides.schemas.guide_read import GuideRead
from app.modules.guides.schemas.guide_update import GuideUpdate
from app.modules.guides.schemas.guide_summary import GuideSummary
from app.modules.files.services.file_service import FileValidationError
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import queue_webhook_event_safely, schedule_webhook_deliveries
from app.modules.guides.services.guide_service import (
    GuideValidationError,
    create_guide,
    delete_guide,
    get_guide,
    list_guides,
    update_guide,
)

router = APIRouter(prefix="/guides", tags=["guides"])


@router.get("", response_model=list[GuideSummary])
def get_guides(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[GuideSummary]:
    return list_guides(db, search=search, category=category)


@router.post("", response_model=GuideRead, status_code=status.HTTP_201_CREATED)
def post_guide(
    payload: GuideCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> GuideRead:
    try:
        guide = create_guide(db, payload, current_user)
    except (FileValidationError, GuideValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db, actor=current_user, entity_type="guide", entity_id=guide.id, action="create",
        summary=f'Guide “{guide.title}” created.',
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="guide.created", resource_type="guide", resource_id=guide.id,
        resource_url=f"/guides/{guide.id}", actor=current_user, data=guide,
    ))
    return guide


@router.get("/{guide_id}", response_model=GuideRead)
def get_guide_detail(
    guide_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> GuideRead:
    guide = get_guide(db, guide_id)
    if guide is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    return guide


@router.put("/{guide_id}", response_model=GuideRead)
def put_guide(
    guide_id: int,
    payload: GuideUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> GuideRead:
    try:
        guide = update_guide(db, guide_id, payload, current_user)
    except (FileValidationError, GuideValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if guide is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="guide", entity_id=guide_id, action="update",
        summary=f'Guide “{guide.title}” updated.',
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="guide.updated", resource_type="guide", resource_id=guide_id,
        resource_url=f"/guides/{guide_id}", actor=current_user, data=guide,
    ))
    return guide


@router.delete("/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_guide(
    guide_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = get_guide(db, guide_id)
    if not delete_guide(db, guide_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="guide", entity_id=guide_id, action="delete",
        summary=f'Guide “{getattr(existing, "title", guide_id)}” deleted.',
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="guide.removed", resource_type="guide", resource_id=guide_id,
        resource_url="/guides", actor=current_user,
        data={"id": guide_id, "title": getattr(existing, "title", str(guide_id))},
    ))
