from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ForumPost, ForumPostAttachment, ForumThread, User
from app.schemas import FileRead, ForumPostCreate, ForumPostRead, ForumThreadCreate, ForumThreadRead, ForumThreadSummary
from app.services.file_service import get_files_for_owner


class ForumValidationError(ValueError):
    pass


def _post_to_read(post: ForumPost) -> ForumPostRead:
    return ForumPostRead(
        id=post.id,
        thread_id=post.thread_id,
        author_id=post.author_id,
        author=post.author,
        body=post.body,
        attachments=[FileRead.model_validate(attachment.file) for attachment in post.attachments],
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _thread_summary(thread: ForumThread) -> ForumThreadSummary:
    return ForumThreadSummary(
        id=thread.id,
        title=thread.title,
        category=thread.category,
        owner_id=thread.owner_id,
        owner=thread.owner,
        reply_count=thread.reply_count,
        last_activity_at=thread.last_activity_at,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


def list_threads(db: Session, search: str | None = None, category: str | None = None) -> list[ForumThreadSummary]:
    statement = (
        select(ForumThread)
        .options(selectinload(ForumThread.posts).selectinload(ForumPost.attachments).selectinload(ForumPostAttachment.file))
        .order_by(ForumThread.updated_at.desc(), ForumThread.id.desc())
    )
    if search:
        like = f"%{search.strip()}%"
        statement = statement.where(ForumThread.title.ilike(like) | ForumThread.category.ilike(like))
    if category:
        statement = statement.where(ForumThread.category == category.strip().lower())
    threads = db.scalars(statement).unique().all()
    return [_thread_summary(thread) for thread in threads]


def get_thread(db: Session, thread_id: int) -> ForumThreadRead | None:
    thread = db.scalar(
        select(ForumThread)
        .options(
            selectinload(ForumThread.posts).selectinload(ForumPost.author),
            selectinload(ForumThread.posts).selectinload(ForumPost.attachments).selectinload(ForumPostAttachment.file),
        )
        .where(ForumThread.id == thread_id)
    )
    if thread is None:
        return None
    summary = _thread_summary(thread)
    return ForumThreadRead(**summary.model_dump(), posts=[_post_to_read(post) for post in thread.posts])


def create_thread(db: Session, payload: ForumThreadCreate, author: User) -> ForumThreadRead:
    files = get_files_for_owner(db, payload.file_ids, author)
    thread = ForumThread(title=payload.title, category=payload.category, owner_id=author.id)
    first_post = ForumPost(body=payload.body, author_id=author.id)
    for index, file in enumerate(files):
        first_post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=index))
    thread.posts.append(first_post)
    db.add(thread)
    db.commit()
    created = get_thread(db, thread.id)
    if created is None:
        raise ForumValidationError("Thread could not be loaded after creation.")
    return created


def add_post(db: Session, thread_id: int, payload: ForumPostCreate, author: User) -> ForumPostRead | None:
    thread = db.get(ForumThread, thread_id)
    if thread is None:
        return None
    files = get_files_for_owner(db, payload.file_ids, author)
    post = ForumPost(thread_id=thread.id, body=payload.body, author_id=author.id)
    for index, file in enumerate(files):
        post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=index))
    db.add(post)
    thread.updated_at = post.created_at
    db.commit()
    db.refresh(post)
    return _post_to_read(post)
