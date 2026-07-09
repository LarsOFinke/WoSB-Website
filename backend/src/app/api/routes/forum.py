from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.models import User
from app.schemas import ForumPostCreate, ForumPostRead, ForumThreadCreate, ForumThreadRead, ForumThreadSummary
from app.services.file_service import FileValidationError
from app.services.forum_service import ForumValidationError, add_post, create_thread, get_thread, list_threads

router = APIRouter(prefix="/forum", tags=["forum"])


@router.get("/threads", response_model=list[ForumThreadSummary])
def get_threads(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
) -> list[ForumThreadSummary]:
    return list_threads(db, search=search, category=category)


@router.post("/threads", response_model=ForumThreadRead, status_code=status.HTTP_201_CREATED)
def post_thread(
    payload: ForumThreadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ForumThreadRead:
    try:
        return create_thread(db, payload, current_user)
    except (FileValidationError, ForumValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/threads/{thread_id}", response_model=ForumThreadRead)
def get_thread_detail(thread_id: int, db: Session = Depends(get_db)) -> ForumThreadRead:
    thread = get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    return thread


@router.post("/threads/{thread_id}/posts", response_model=ForumPostRead, status_code=status.HTTP_201_CREATED)
def post_reply(
    thread_id: int,
    payload: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ForumPostRead:
    try:
        post = add_post(db, thread_id, payload, current_user)
    except FileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    return post
