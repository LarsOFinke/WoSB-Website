from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.accounts.models.user import User
from app.modules.builds.models.build import Build
from app.modules.guides.models.guide import Guide
from app.modules.onboarding.models.newcomer_guide import (
    NewcomerGuideBlock,
    NewcomerGuidePage,
    NewcomerGuideResource,
)
from app.modules.onboarding.schemas.newcomer_guide import (
    NewcomerGuideBlockRead,
    NewcomerGuideRead,
    NewcomerGuideResourceRead,
    NewcomerGuideUpdate,
)

PAGE_ID = 1


class NewcomerGuideValidationError(ValueError):
    pass


def _page_query():
    return select(NewcomerGuidePage).options(
        selectinload(NewcomerGuidePage.blocks).selectinload(NewcomerGuideBlock.resources),
        selectinload(NewcomerGuidePage.updated_by),
    )


def get_page_model(db: Session) -> NewcomerGuidePage | None:
    return db.scalar(_page_query().where(NewcomerGuidePage.id == PAGE_ID))


def _validated_href(resource_type: str, url: str | None) -> str:
    value = (url or "").strip()
    if resource_type == "internal":
        if not value.startswith("/") or value.startswith("//"):
            raise NewcomerGuideValidationError("Internal links must start with a single '/'.")
        return value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise NewcomerGuideValidationError("External links must use a complete http(s) URL.")
    return value


def _resource_read(db: Session, resource: NewcomerGuideResource) -> NewcomerGuideResourceRead:
    label = resource.label or ""
    description = resource.description
    href = "#"
    available = True

    if resource.resource_type == "guide":
        guide = db.get(Guide, resource.resource_id) if resource.resource_id else None
        available = bool(guide and guide.is_published)
        if guide:
            label = label or guide.title
            description = description or guide.summary
            href = f"/guides/{guide.id}"
    elif resource.resource_type == "build":
        build = db.get(Build, resource.resource_id) if resource.resource_id else None
        available = build is not None
        if build:
            label = label or build.build_name
            href = f"/builds/{build.id}"
    else:
        href = _validated_href(resource.resource_type, resource.url)
        label = label or href

    return NewcomerGuideResourceRead(
        id=resource.id,
        resource_type=resource.resource_type,
        resource_id=resource.resource_id,
        label=label or "Unavailable resource",
        description=description,
        href=href,
        available=available,
    )


def serialize_page(db: Session, page: NewcomerGuidePage) -> NewcomerGuideRead:
    blocks = [
        NewcomerGuideBlockRead(
            id=block.id,
            block_type=block.block_type,
            title=block.title,
            body=block.body,
            resources=[_resource_read(db, resource) for resource in block.resources],
        )
        for block in page.blocks
    ]
    return NewcomerGuideRead(
        id=page.id,
        title=page.title,
        intro=page.intro,
        blocks=blocks,
        updated_at=page.updated_at,
        updated_by=page.updated_by.display_name if page.updated_by else None,
    )


def get_newcomer_guide(db: Session) -> NewcomerGuideRead:
    page = get_page_model(db)
    if page is None:
        page = NewcomerGuidePage(
            id=PAGE_ID,
            title="New Captain Guide",
            intro="A curated route from first login to prepared fleet participation.",
        )
        db.add(page)
        db.commit()
        page = get_page_model(db)
    if page is None:
        raise NewcomerGuideValidationError("The newcomer guide could not be initialized.")
    return serialize_page(db, page)


def _validate_resource_target(db: Session, resource_type: str, resource_id: int | None, url: str | None) -> None:
    if resource_type == "guide":
        guide = db.get(Guide, resource_id) if resource_id else None
        if guide is None or not guide.is_published:
            raise NewcomerGuideValidationError("The selected guide does not exist or is not published.")
    elif resource_type == "build":
        if not resource_id or db.get(Build, resource_id) is None:
            raise NewcomerGuideValidationError("The selected build does not exist.")
    else:
        _validated_href(resource_type, url)


def update_newcomer_guide(
    db: Session,
    payload: NewcomerGuideUpdate,
    editor: User,
) -> NewcomerGuideRead:
    page = get_page_model(db)
    if page is None:
        page = NewcomerGuidePage(id=PAGE_ID, title=payload.title, intro=payload.intro)
        db.add(page)
        db.flush()

    page.title = payload.title
    page.intro = payload.intro
    page.updated_by_id = editor.id
    page.updated_by = editor
    page.blocks.clear()

    for block_index, block_payload in enumerate(payload.blocks, start=1):
        block = NewcomerGuideBlock(
            block_type=block_payload.block_type,
            title=block_payload.title,
            body=block_payload.body,
            sort_order=block_index * 10,
        )
        for resource_index, resource_payload in enumerate(block_payload.resources, start=1):
            _validate_resource_target(
                db,
                resource_payload.resource_type,
                resource_payload.resource_id,
                resource_payload.url,
            )
            block.resources.append(
                NewcomerGuideResource(
                    resource_type=resource_payload.resource_type,
                    resource_id=resource_payload.resource_id,
                    label=resource_payload.label,
                    description=resource_payload.description,
                    url=resource_payload.url,
                    sort_order=resource_index * 10,
                )
            )
        page.blocks.append(block)

    db.commit()
    refreshed = get_page_model(db)
    if refreshed is None:
        raise NewcomerGuideValidationError("The newcomer guide could not be loaded after saving.")
    return serialize_page(db, refreshed)
