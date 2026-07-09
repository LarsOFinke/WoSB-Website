from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Build, BuildSlot, Guide, GuideAttachment, GuideBuildReference, User
from app.schemas import BuildRead, FileRead, GuideCreate, GuideRead, GuideSummary
from app.services.content_embed_service import ContentEmbedValidationError, validate_build_embeds, validate_content_embeds
from app.services.file_service import get_files_for_owner


class GuideValidationError(ValueError):
    pass


def _validate_guide_embeds(body: str, files, builds) -> None:
    try:
        validate_content_embeds(body, files)
        validate_build_embeds(body, builds)
    except ContentEmbedValidationError as exc:
        raise GuideValidationError(str(exc)) from exc


def _load_linked_builds(db: Session, build_ids: list[int]) -> list[Build]:
    if not build_ids:
        return []
    statement = (
        select(Build)
        .options(selectinload(Build.slots).selectinload(BuildSlot.option))
        .where(Build.id.in_(build_ids))
    )
    builds_by_id = {build.id: build for build in db.scalars(statement).unique().all()}
    missing = [build_id for build_id in build_ids if build_id not in builds_by_id]
    if missing:
        raise GuideValidationError("One or more selected builds could not be found.")
    return [builds_by_id[build_id] for build_id in build_ids]


def _guide_options():
    return (
        selectinload(Guide.attachments).selectinload(GuideAttachment.file),
        selectinload(Guide.build_references)
        .selectinload(GuideBuildReference.build)
        .selectinload(Build.slots)
        .selectinload(BuildSlot.option),
    )


def _guide_summary(guide: Guide) -> GuideSummary:
    return GuideSummary(
        id=guide.id,
        title=guide.title,
        category=guide.category,
        summary=guide.summary,
        owner_id=guide.owner_id,
        owner=guide.owner,
        attachment_count=len(guide.attachments),
        build_reference_count=len(guide.build_references),
        created_at=guide.created_at,
        updated_at=guide.updated_at,
    )


def _guide_read(guide: Guide) -> GuideRead:
    summary = _guide_summary(guide)
    builds = [BuildRead.model_validate(item.build) for item in guide.build_references]
    return GuideRead(
        **summary.model_dump(),
        body=guide.body,
        attachments=[FileRead.model_validate(item.file) for item in guide.attachments],
        builds=builds,
    )


def list_guides(db: Session, search: str | None = None, category: str | None = None) -> list[GuideSummary]:
    statement = (
        select(Guide)
        .options(*_guide_options())
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
    guide = db.scalar(select(Guide).options(*_guide_options()).where(Guide.id == guide_id, Guide.is_published.is_(True)))
    return _guide_read(guide) if guide else None


def create_guide(db: Session, payload: GuideCreate, author: User) -> GuideRead:
    files = get_files_for_owner(db, payload.file_ids, author)
    builds = _load_linked_builds(db, payload.build_ids)
    _validate_guide_embeds(payload.body, files, builds)
    guide = Guide(
        title=payload.title,
        category=payload.category,
        summary=payload.summary,
        body=payload.body,
        owner_id=author.id,
    )
    for index, file in enumerate(files):
        guide.attachments.append(GuideAttachment(file_id=file.id, sort_order=index))
    for index, build in enumerate(builds):
        guide.build_references.append(GuideBuildReference(build_id=build.id, sort_order=index))
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
