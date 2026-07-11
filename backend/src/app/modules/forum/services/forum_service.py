from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.constants import normalize_forum_category
from app.modules.accounts.models.user import User
from app.modules.forum.models.forum import ForumThread
from app.modules.forum.models.forum_post import ForumPost
from app.modules.forum.models.forum_post_attachment import ForumPostAttachment
from app.modules.files.schemas.file_asset import FileRead
from app.modules.forum.schemas.forum_post_create import ForumPostCreate
from app.modules.forum.schemas.forum_post_read import ForumPostRead
from app.modules.forum.schemas.forum_post_update import ForumPostUpdate
from app.modules.forum.schemas.forum_thread_create import ForumThreadCreate
from app.modules.forum.schemas.forum_thread_read import ForumThreadRead
from app.modules.forum.schemas.forum_thread_summary import ForumThreadSummary
from app.modules.forum.schemas.forum_thread_update import ForumThreadUpdate
from app.modules.content.services.content_embed_service import ContentEmbedValidationError, validate_content_embeds
from app.modules.files.services.file_service import get_files_for_owner


class ForumValidationError(ValueError):
    pass


def _validate_post_embeds(body: str, files) -> None:
    try:
        validate_content_embeds(body, files)
    except ContentEmbedValidationError as exc:
        raise ForumValidationError(str(exc)) from exc


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
        category=normalize_forum_category(thread.category),
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
        statement = statement.where(ForumThread.category == normalize_forum_category(category))
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
    _validate_post_embeds(payload.body, files)
    thread = ForumThread(title=payload.title, category=normalize_forum_category(payload.category), owner_id=author.id)
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
    _validate_post_embeds(payload.body, files)
    post = ForumPost(thread_id=thread.id, body=payload.body, author_id=author.id)
    for index, file in enumerate(files):
        post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=index))
    db.add(post)
    # ``post.created_at`` is populated only during flush. Assigning it before
    # that point wrote NULL into the non-nullable thread timestamp and caused
    # replies to fail with HTTP 500. Use one explicit activity timestamp for
    # both records instead.
    activity_at = datetime.utcnow()
    post.created_at = activity_at
    post.updated_at = activity_at
    thread.updated_at = activity_at
    db.commit()
    db.refresh(post)
    return _post_to_read(post)


def update_thread(
    db: Session, thread_id: int, payload: ForumThreadUpdate, user: User
) -> ForumThreadRead | None:
    thread = db.scalar(
        select(ForumThread)
        .options(
            selectinload(ForumThread.posts).selectinload(ForumPost.author),
            selectinload(ForumThread.posts)
            .selectinload(ForumPost.attachments)
            .selectinload(ForumPostAttachment.file),
        )
        .where(ForumThread.id == thread_id)
    )
    if thread is None or (thread.owner_id != user.id and not user.can_moderate):
        return None
    if not thread.posts:
        raise ForumValidationError("Thread has no opening post.")

    files = get_files_for_owner(db, payload.file_ids, user)
    _validate_post_embeds(payload.body, files)
    opening_post = thread.posts[0]
    activity_at = datetime.utcnow()

    thread.title = payload.title
    thread.category = normalize_forum_category(payload.category)
    thread.updated_at = activity_at
    opening_post.body = payload.body
    opening_post.updated_at = activity_at
    opening_post.attachments.clear()
    for index, file in enumerate(files):
        opening_post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=index))

    db.commit()
    updated = get_thread(db, thread.id)
    if updated is None:
        raise ForumValidationError("Thread could not be loaded after update.")
    return updated


def update_post(
    db: Session, post_id: int, payload: ForumPostUpdate, user: User
) -> ForumPostRead | None:
    post = db.scalar(
        select(ForumPost)
        .options(
            selectinload(ForumPost.author),
            selectinload(ForumPost.attachments).selectinload(ForumPostAttachment.file),
        )
        .where(ForumPost.id == post_id)
    )
    if post is None or (post.author_id != user.id and not user.can_moderate):
        return None

    files = get_files_for_owner(db, payload.file_ids, user)
    _validate_post_embeds(payload.body, files)
    activity_at = datetime.utcnow()
    post.body = payload.body
    post.updated_at = activity_at
    post.attachments.clear()
    for index, file in enumerate(files):
        post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=index))

    thread = db.get(ForumThread, post.thread_id)
    if thread is not None:
        thread.updated_at = activity_at
    db.commit()

    updated = db.scalar(
        select(ForumPost)
        .options(
            selectinload(ForumPost.author),
            selectinload(ForumPost.attachments).selectinload(ForumPostAttachment.file),
        )
        .where(ForumPost.id == post.id)
    )
    if updated is None:
        raise ForumValidationError("Post could not be loaded after update.")
    return _post_to_read(updated)


def delete_thread(db: Session, thread_id: int, user: User) -> bool:
    thread = db.get(ForumThread, thread_id)
    if thread is None or (thread.owner_id != user.id and not user.can_moderate):
        return False
    db.delete(thread)
    db.commit()
    return True
