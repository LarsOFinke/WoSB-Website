from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.builds.models.build import Build
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.guides.models.guide import Guide
from app.modules.guides.models.guide_attachment import GuideAttachment
from app.modules.guides.models.guide_build_reference import GuideBuildReference
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.files.schemas.file_asset import FileRead
from app.modules.files.services.file_cleanup_service import (
    remove_stored_file_paths,
    stage_unreferenced_files_for_deletion,
)
from app.modules.guides.schemas.guide_create import GuideCreate
from app.modules.guides.schemas.guide_read import GuideRead
from app.modules.guides.schemas.guide_update import GuideUpdate
from app.modules.guides.schemas.guide_summary import GuideSummary
from app.modules.content.services.content_embed_service import ContentEmbedValidationError, validate_build_embeds, validate_content_embeds
from app.modules.files.services.file_service import (
    get_files_for_owner,
    publish_files,
    refresh_file_publication,
)


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


def _guide_summary(
    guide: Guide,
    attachment_count: int | None = None,
    build_reference_count: int | None = None,
) -> GuideSummary:
    return GuideSummary(
        id=guide.id,
        title=guide.title,
        category=guide.category,
        summary=guide.summary,
        owner_id=guide.owner_id,
        owner=guide.owner,
        attachment_count=len(guide.attachments) if attachment_count is None else attachment_count,
        build_reference_count=(
            len(guide.build_references)
            if build_reference_count is None
            else build_reference_count
        ),
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
    attachment_count = (
        select(func.count(GuideAttachment.id))
        .where(GuideAttachment.guide_id == Guide.id)
        .correlate(Guide)
        .scalar_subquery()
    )
    build_reference_count = (
        select(func.count(GuideBuildReference.id))
        .where(GuideBuildReference.guide_id == Guide.id)
        .correlate(Guide)
        .scalar_subquery()
    )
    statement = (
        select(Guide, attachment_count, build_reference_count)
        .where(Guide.is_published.is_(True))
        .order_by(Guide.updated_at.desc(), Guide.id.desc())
    )
    if search:
        like = f"%{search.strip()}%"
        statement = statement.where(Guide.title.ilike(like) | Guide.summary.ilike(like) | Guide.body.ilike(like))
    if category:
        statement = statement.where(Guide.category == category.strip().lower())
    return [
        _guide_summary(
            guide,
            attachment_count=int(file_count or 0),
            build_reference_count=int(build_count or 0),
        )
        for guide, file_count, build_count in db.execute(statement).unique().all()
    ]


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
    publish_files(files, "guide")
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


def update_guide(db: Session, guide_id: int, payload: GuideUpdate, user: User) -> GuideRead | None:
    guide = db.scalar(select(Guide).options(*_guide_options()).where(Guide.id == guide_id, Guide.is_published.is_(True)))
    if guide is None or (guide.owner_id != user.id and not user.can_moderate):
        return None

    files = get_files_for_owner(db, payload.file_ids, user)
    builds = _load_linked_builds(db, payload.build_ids)
    _validate_guide_embeds(payload.body, files, builds)

    previous_file_ids = {attachment.file_id for attachment in guide.attachments}
    guide.title = payload.title
    guide.category = payload.category
    guide.summary = payload.summary
    guide.body = payload.body
    guide.attachments.clear()
    guide.build_references.clear()
    publish_files(files, "guide")
    for index, file in enumerate(files):
        guide.attachments.append(GuideAttachment(file_id=file.id, sort_order=index))
    for index, build in enumerate(builds):
        guide.build_references.append(GuideBuildReference(build_id=build.id, sort_order=index))

    refresh_file_publication(db, previous_file_ids | {file.id for file in files})
    db.commit()
    updated = get_guide(db, guide.id)
    if updated is None:
        raise GuideValidationError("Guide could not be loaded after update.")
    return updated


def delete_guide(db: Session, guide_id: int, user: User) -> bool:
    guide = db.get(Guide, guide_id)
    if guide is None or (guide.owner_id != user.id and not user.can_moderate):
        return False
    file_ids = {attachment.file_id for attachment in guide.attachments}
    guide.attachments.clear()
    guide.build_references.clear()
    guide.is_published = False
    db.flush()
    refresh_file_publication(db, file_ids)
    paths = stage_unreferenced_files_for_deletion(db, file_ids)
    db.commit()
    remove_stored_file_paths(paths)
    return True
