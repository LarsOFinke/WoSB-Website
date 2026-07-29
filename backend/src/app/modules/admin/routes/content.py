from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.builds.schemas.build_role import (
    BuildRoleAssignment,
    BuildRoleCreate,
    BuildRoleRead,
    BuildRoleUpdate,
)
from app.modules.builds.services.build_role_service import (
    BuildRoleError,
    assign_build_role,
    create_build_role,
    delete_build_role,
    list_build_roles,
    update_build_role,
)
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
    current_user: User = Depends(require_staff),
) -> list[BuildRead]:
    return list_builds(db, search=search, build_type=build_type, viewer_id=current_user.id)


@router.get("/build-roles", response_model=list[BuildRoleRead])
def admin_list_build_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[BuildRoleRead]:
    return list_build_roles(db)


@router.post("/build-roles", response_model=BuildRoleRead, status_code=status.HTTP_201_CREATED)
def admin_create_build_role(
    payload: BuildRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> BuildRoleRead:
    try:
        role = create_build_role(db, payload)
    except BuildRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build_role",
        entity_id=role.slug,
        action="create",
        summary=f'Build role “{role.label}” created.',
        changed_fields=list(payload.model_dump().keys()),
    )
    return role


@router.put("/build-roles/{slug}", response_model=BuildRoleRead)
def admin_update_build_role(
    slug: str,
    payload: BuildRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> BuildRoleRead:
    try:
        role = update_build_role(db, slug, payload)
    except BuildRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build_role",
        entity_id=role.slug,
        action="update",
        summary=f'Build role “{role.label}” updated.',
        changed_fields=list(payload.model_dump().keys()),
    )
    return role


@router.delete("/build-roles/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_build_role(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    try:
        delete_build_role(db, slug)
    except BuildRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build_role",
        entity_id=slug,
        action="delete",
        summary=f'Build role “{slug}” deleted.',
    )


@router.put("/builds/{build_id}/role", response_model=BuildRead)
def admin_assign_build_role(
    build_id: int,
    payload: BuildRoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> BuildRead:
    try:
        build = assign_build_role(db, build_id, payload.build_type)
    except BuildRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    build = get_build(db, build_id, viewer_id=current_user.id) or build
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build",
        entity_id=build_id,
        action="update_role",
        summary=f'Build “{build.build_name}” assigned to role “{build.build_role_label}”.',
        changed_fields=["build_type"],
    )
    return build


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
    background_tasks: BackgroundTasks,
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
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="forum.thread.removed", resource_type="forum_thread", resource_id=thread_id,
        resource_url="/forum", actor=current_user,
        data={"id": thread_id, "title": getattr(existing, "title", str(thread_id))},
        **webhook_event_scope(db, use_primary_fleet=True),
    ))


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
