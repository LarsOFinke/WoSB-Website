from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.forum.schemas.forum_post_create import ForumPostCreate
from app.modules.forum.schemas.forum_post_read import ForumPostRead
from app.modules.forum.schemas.forum_post_update import ForumPostUpdate
from app.modules.forum.schemas.forum_thread_create import ForumThreadCreate
from app.modules.forum.schemas.forum_thread_read import ForumThreadRead
from app.modules.forum.schemas.forum_thread_summary import ForumThreadSummary
from app.modules.forum.schemas.forum_thread_update import ForumThreadUpdate
from app.modules.files.services.file_service import FileValidationError
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope
from app.modules.forum.services.forum_service import (
    ForumValidationError,
    add_post,
    create_thread,
    delete_post,
    get_thread,
    list_threads,
    update_post,
    update_thread,
)

router = APIRouter(prefix="/forum", tags=["forum"])


@router.get("/threads", response_model=list[ForumThreadSummary])
def get_threads(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[ForumThreadSummary]:
    return list_threads(db, search=search, category=category)


@router.post("/threads", response_model=ForumThreadRead, status_code=status.HTTP_201_CREATED)
def post_thread(
    payload: ForumThreadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ForumThreadRead:
    try:
        thread = create_thread(db, payload, current_user)
    except (FileValidationError, ForumValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db, actor=current_user, entity_type="forum_thread", entity_id=thread.id, action="create",
        summary=f'Forum thread “{thread.title}” created.',
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="forum.thread.created", resource_type="forum_thread", resource_id=thread.id,
        resource_url=f"/forum/{thread.id}", actor=current_user, data=thread,
        **webhook_event_scope(db, use_primary_fleet=True),
    ))
    return thread


@router.get("/threads/{thread_id}", response_model=ForumThreadRead)
def get_thread_detail(
    thread_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> ForumThreadRead:
    thread = get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    return thread


@router.put("/threads/{thread_id}", response_model=ForumThreadRead)
def put_thread(
    thread_id: int,
    payload: ForumThreadUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ForumThreadRead:
    try:
        thread = update_thread(db, thread_id, payload, current_user)
    except (FileValidationError, ForumValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="forum_thread", entity_id=thread_id, action="update",
        summary=f'Forum thread “{thread.title}” updated.',
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="forum.thread.updated", resource_type="forum_thread", resource_id=thread_id,
        resource_url=f"/forum/{thread_id}", actor=current_user, data=thread,
        **webhook_event_scope(db, use_primary_fleet=True),
    ))
    return thread


@router.post("/threads/{thread_id}/posts", response_model=ForumPostRead, status_code=status.HTTP_201_CREATED)
def post_reply(
    thread_id: int,
    payload: ForumPostCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ForumPostRead:
    try:
        post = add_post(db, thread_id, payload, current_user)
    except (FileValidationError, ForumValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="forum_post", entity_id=post.id, action="create",
        summary=f'Forum reply added to thread #{thread_id}.',
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="forum.post.created", resource_type="forum_post", resource_id=post.id,
        resource_url=f"/forum/{thread_id}", actor=current_user, data=post,
        **webhook_event_scope(db, use_primary_fleet=True),
    ))
    return post


@router.put("/posts/{post_id}", response_model=ForumPostRead)
def put_post(
    post_id: int,
    payload: ForumPostUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ForumPostRead:
    try:
        post = update_post(db, post_id, payload, current_user)
    except (FileValidationError, ForumValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="forum_post", entity_id=post_id, action="update",
        summary=f'Forum post #{post_id} updated.',
        changed_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="forum.post.updated", resource_type="forum_post", resource_id=post.id,
        resource_url=f"/forum/{post.thread_id}", actor=current_user, data=post,
        **webhook_event_scope(db, use_primary_fleet=True),
    ))
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forum_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    try:
        post = delete_post(db, post_id, current_user)
    except ForumValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="forum_post", entity_id=post_id, action="delete",
        summary=f'Forum post #{post_id} removed from thread #{post.thread_id}.',
    )
    schedule_webhook_deliveries(background_tasks, queue_webhook_event_safely(
        db, event_type="forum.post.removed", resource_type="forum_post", resource_id=post.id,
        resource_url=f"/forum/{post.thread_id}", actor=current_user, data=post,
        **webhook_event_scope(db, use_primary_fleet=True),
    ))
