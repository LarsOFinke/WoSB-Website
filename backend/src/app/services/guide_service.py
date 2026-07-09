from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Guide, GuideAttachment, User
from app.schemas import FileRead, GuideCreate, GuideRead, GuideSummary
from app.services.file_service import get_files_for_owner


class GuideValidationError(ValueError):
    pass


def _guide_summary(guide: Guide) -> GuideSummary:
    return GuideSummary(
        id=guide.id,
        title=guide.title,
        category=guide.category,
        summary=guide.summary,
        owner_id=guide.owner_id,
        owner=guide.owner,
        attachment_count=len(guide.attachments),
        created_at=guide.created_at,
        updated_at=guide.updated_at,
    )


def _guide_read(guide: Guide) -> GuideRead:
    summary = _guide_summary(guide)
    return GuideRead(**summary.model_dump(), body=guide.body, attachments=[FileRead.model_validate(item.file) for item in guide.attachments])


def list_guides(db: Session, search: str | None = None, category: str | None = None) -> list[GuideSummary]:
    statement = (
        select(Guide)
        .options(selectinload(Guide.attachments).selectinload(GuideAttachment.file))
        .where(Guide.is_published.is_(True))
        .order_by(Guide.updated_at.desc(), Guide.id.desc())
    )
    if search:
        like = f"%{search.strip()}%"
        statement = statement.where(Guide.title.ilike(like) | Guide.summary.ilike(like) | Guide.body.ilike(like))
    if category:
        statement = statement.where(Guide.category == category.strip().lower())
    return [_guide_summary(guide) for guide in db.scalars(statement).unique().all()]


def get_guide(db: Session, guide_id: int) -> GuideRead | None:
    guide = db.scalar(
        select(Guide)
        .options(selectinload(Guide.attachments).selectinload(GuideAttachment.file))
        .where(Guide.id == guide_id, Guide.is_published.is_(True))
    )
    return _guide_read(guide) if guide else None


def create_guide(db: Session, payload: GuideCreate, author: User) -> GuideRead:
    files = get_files_for_owner(db, payload.file_ids, author)
    guide = Guide(
        title=payload.title,
        category=payload.category,
        summary=payload.summary,
        body=payload.body,
        owner_id=author.id,
    )
    for index, file in enumerate(files):
        guide.attachments.append(GuideAttachment(file_id=file.id, sort_order=index))
    db.add(guide)
    db.commit()
    created = get_guide(db, guide.id)
    if created is None:
        raise GuideValidationError("Guide could not be loaded after creation.")
    return created


def delete_guide(db: Session, guide_id: int, user: User) -> bool:
    guide = db.get(Guide, guide_id)
    if guide is None or (guide.owner_id != user.id and not user.can_moderate):
        return False
    guide.is_published = False
    db.commit()
    return True
