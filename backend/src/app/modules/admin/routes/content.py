from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.builds.services.build_service import delete_build, get_build, list_builds
from app.modules.forum.schemas.forum_thread_summary import ForumThreadSummary
from app.modules.forum.services.forum_service import delete_thread, get_thread, list_threads
from app.modules.guides.schemas.guide_summary import GuideSummary
from app.modules.guides.services.guide_service import delete_guide, get_guide, list_guides

router = APIRouter(tags=["admin-content"])


@router.get("/builds", response_model=list[BuildRead])
def admin_list_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[BuildRead]:
    return list_builds(db, search=search, build_type=build_type)


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    existing = get_build(db, build_id)
    if not delete_build(db, build_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build",
        entity_id=build_id,
        action="delete",
        summary=f'Build “{getattr(existing, "build_name", build_id)}” removed by staff.',
    )


@router.get("/forum/threads", response_model=list[ForumThreadSummary])
def admin_list_forum_threads(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[ForumThreadSummary]:
    return list_threads(db, search=search, category=category)


@router.delete("/forum/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_forum_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    existing = get_thread(db, thread_id)
    if not delete_thread(db, thread_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum thread not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="forum_thread",
        entity_id=thread_id,
        action="delete",
        summary=f'Forum thread “{getattr(existing, "title", thread_id)}” removed by staff.',
    )


@router.get("/guides", response_model=list[GuideSummary])
def admin_list_guides(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[GuideSummary]:
    return list_guides(db, search=search, category=category)


@router.delete("/guides/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_guide(
    guide_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    existing = get_guide(db, guide_id)
    if not delete_guide(db, guide_id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="guide",
        entity_id=guide_id,
        action="delete",
        summary=f'Guide “{getattr(existing, "title", guide_id)}” removed by staff.',
    )
