from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.secret_box import webhook_secret_box
from app.modules.accounts.models.user import User
from app.modules.raid_helper.models.raid_helper import (
    RaidHelperDestination,
    RaidHelperDestinationCategory,
    RaidHelperEventLink,
    RaidHelperProfile,
    RaidHelperTemplate,
    RaidHelperTemplateCategory,
)
from app.modules.raid_helper.schemas.raid_helper import (
    RaidHelperDestinationRead,
    RaidHelperDestinationWrite,
    RaidHelperProfileCreate,
    RaidHelperProfileRead,
    RaidHelperProfileWrite,
    RaidHelperTemplateRead,
    RaidHelperTemplateWrite,
)
from app.modules.raid_helper.services.errors import RaidHelperError
from app.modules.squads.services.squad_service import get_squad_model

_ALLOWED_API_HOSTS = {
    "raid-helper.dev",
    "www.raid-helper.dev",
    "raid-helper.xyz",
    "www.raid-helper.xyz",
}


def _validate_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_API_HOSTS:
        raise RaidHelperError("Raid-Helper API URL must use an official HTTPS host.")
    path = parsed.path.rstrip("/")
    if not path.endswith("/api/v4"):
        raise RaidHelperError("Raid-Helper API URL must end with /api/v4.")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise RaidHelperError("Raid-Helper API URL contains unsupported components.")
    return f"https://{parsed.hostname}{path}"

def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise RaidHelperError("Raid-Helper timezone must be a valid IANA timezone.") from exc
    return value


def _profile_read(row: RaidHelperProfile) -> RaidHelperProfileRead:
    return RaidHelperProfileRead(
        id=row.id,
        name=row.name,
        server_id=row.server_id,
        api_base_url=row.api_base_url,
        authorization_mode=row.authorization_mode,
        timezone=row.timezone,
        is_active=row.is_active,
        api_key_configured=bool(row.api_key_encrypted),
        created_by_username=row.created_by_username,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_profiles(db: Session) -> list[RaidHelperProfileRead]:
    return [_profile_read(row) for row in db.scalars(select(RaidHelperProfile).order_by(RaidHelperProfile.name)).all()]


def create_profile(db: Session, payload: RaidHelperProfileCreate, actor: User) -> RaidHelperProfileRead:
    base = _validate_base_url(payload.api_base_url)
    row = RaidHelperProfile(
        name=payload.name,
        server_id=payload.server_id,
        api_key_encrypted=webhook_secret_box.encrypt(payload.api_key),
        api_base_url=base,
        authorization_mode=payload.authorization_mode,
        timezone=_validate_timezone(payload.timezone),
        is_active=payload.is_active,
        created_by_username=actor.username,
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise RaidHelperError("A Raid-Helper profile with this name already exists.") from exc
    db.refresh(row)
    return _profile_read(row)


def update_profile(db: Session, profile_id: int, payload: RaidHelperProfileWrite) -> RaidHelperProfileRead | None:
    row = db.get(RaidHelperProfile, profile_id)
    if row is None:
        return None
    if _profile_has_links(db, profile_id) and row.server_id != payload.server_id:
        raise RaidHelperError("A profile with synchronized events cannot change its server ID; create a new profile instead.")
    row.name = payload.name
    row.server_id = payload.server_id
    row.api_base_url = _validate_base_url(payload.api_base_url)
    row.authorization_mode = payload.authorization_mode
    row.timezone = _validate_timezone(payload.timezone)
    row.is_active = payload.is_active
    if payload.api_key:
        row.api_key_encrypted = webhook_secret_box.encrypt(payload.api_key)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise RaidHelperError("A Raid-Helper profile with this name already exists.") from exc
    db.refresh(row)
    return _profile_read(row)


def _profile_has_links(db: Session, profile_id: int) -> bool:
    return db.scalar(
        select(RaidHelperEventLink.id)
        .join(RaidHelperDestination, RaidHelperEventLink.destination_id == RaidHelperDestination.id)
        .where(RaidHelperDestination.profile_id == profile_id)
        .limit(1)
    ) is not None


def _destination_has_links(db: Session, destination_id: int) -> bool:
    return db.scalar(
        select(RaidHelperEventLink.id)
        .where(RaidHelperEventLink.destination_id == destination_id)
        .limit(1)
    ) is not None


def _template_has_links(db: Session, template_id: int) -> bool:
    return db.scalar(
        select(RaidHelperEventLink.id)
        .where(RaidHelperEventLink.template_id == template_id)
        .limit(1)
    ) is not None


def delete_profile(db: Session, profile_id: int) -> bool:
    row = db.get(RaidHelperProfile, profile_id)
    if row is None:
        return False
    if _profile_has_links(db, profile_id):
        raise RaidHelperError("Profiles with synchronized calendar events cannot be deleted; deactivate them instead.")
    db.delete(row)
    db.commit()
    return True


def _replace_categories(db: Session, relationship: list[Any], model: type, foreign_key: str, row_id: int, categories: list[str]) -> None:
    relationship.clear()
    for category in categories:
        relationship.append(model(**{foreign_key: row_id, "category": category}))


def _destination_read(row: RaidHelperDestination) -> RaidHelperDestinationRead:
    return RaidHelperDestinationRead(
        id=row.id,
        profile_id=row.profile_id,
        profile_name=row.profile.name,
        name=row.name,
        channel_id=row.channel_id,
        scope_type=row.scope_type,
        squad_id=row.squad_id,
        squad_name=row.squad.name if row.squad else None,
        categories=[item.category for item in row.categories],
        is_default=row.is_default,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_destinations(db: Session) -> list[RaidHelperDestinationRead]:
    rows = db.scalars(select(RaidHelperDestination).order_by(RaidHelperDestination.name)).unique().all()
    return [_destination_read(row) for row in rows]


def save_destination(db: Session, payload: RaidHelperDestinationWrite, destination_id: int | None = None) -> RaidHelperDestinationRead:
    profile = db.get(RaidHelperProfile, payload.profile_id)
    if profile is None:
        raise RaidHelperError("Raid-Helper profile not found.")
    if payload.squad_id is not None:
        squad = get_squad_model(db, payload.squad_id)
        if squad is None or not squad.is_active:
            raise RaidHelperError("Squad not found or archived.")
    row = db.get(RaidHelperDestination, destination_id) if destination_id else RaidHelperDestination()
    if row is None:
        raise RaidHelperError("Raid-Helper destination not found.")
    if destination_id is not None and _destination_has_links(db, destination_id):
        current_target = (row.profile_id, row.channel_id, row.scope_type, row.squad_id)
        requested_target = (payload.profile_id, payload.channel_id, payload.scope_type, payload.squad_id)
        if current_target != requested_target:
            raise RaidHelperError("A destination with synchronized events cannot change profile, channel or scope; create a new destination instead.")
    row.profile_id = payload.profile_id
    row.name = payload.name
    row.channel_id = payload.channel_id
    row.scope_type = payload.scope_type
    row.squad_id = payload.squad_id
    row.is_default = payload.is_default
    row.is_active = payload.is_active
    if destination_id is None:
        db.add(row)
        db.flush()
    _replace_categories(db, row.categories, RaidHelperDestinationCategory, "destination_id", row.id, payload.categories)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise RaidHelperError("This profile, channel and scope combination already exists.") from exc
    db.refresh(row)
    return _destination_read(row)


def delete_destination(db: Session, destination_id: int) -> bool:
    row = db.get(RaidHelperDestination, destination_id)
    if row is None:
        return False
    if _destination_has_links(db, destination_id):
        raise RaidHelperError("Destinations with synchronized events cannot be deleted; deactivate them instead.")
    db.delete(row)
    db.commit()
    return True


def _template_read(row: RaidHelperTemplate) -> RaidHelperTemplateRead:
    return RaidHelperTemplateRead(
        id=row.id,
        profile_id=row.profile_id,
        profile_name=row.profile.name,
        name=row.name,
        raid_template_id=row.raid_template_id,
        scope_type=row.scope_type,
        categories=[item.category for item in row.categories],
        title_template=row.title_template,
        description_template=row.description_template,
        announcement_template=row.announcement_template,
        payload_template_json=row.payload_template_json,
        is_default=row.is_default,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_templates(db: Session) -> list[RaidHelperTemplateRead]:
    rows = db.scalars(select(RaidHelperTemplate).order_by(RaidHelperTemplate.name)).unique().all()
    return [_template_read(row) for row in rows]


def save_template(db: Session, payload: RaidHelperTemplateWrite, template_id: int | None = None) -> RaidHelperTemplateRead:
    if db.get(RaidHelperProfile, payload.profile_id) is None:
        raise RaidHelperError("Raid-Helper profile not found.")
    row = db.get(RaidHelperTemplate, template_id) if template_id else RaidHelperTemplate()
    if row is None:
        raise RaidHelperError("Raid-Helper template not found.")
    if template_id is not None and _template_has_links(db, template_id) and row.profile_id != payload.profile_id:
        raise RaidHelperError("A template used by synchronized events cannot move to another profile; create a new template instead.")
    for field in ("profile_id", "name", "raid_template_id", "scope_type", "title_template", "description_template", "announcement_template", "payload_template_json", "is_default", "is_active"):
        setattr(row, field, getattr(payload, field))
    if template_id is None:
        db.add(row)
        db.flush()
    _replace_categories(db, row.categories, RaidHelperTemplateCategory, "template_id", row.id, payload.categories)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise RaidHelperError("A template with this name already exists in the selected profile.") from exc
    db.refresh(row)
    return _template_read(row)


def delete_template(db: Session, template_id: int) -> bool:
    row = db.get(RaidHelperTemplate, template_id)
    if row is None:
        return False
    if _template_has_links(db, template_id):
        raise RaidHelperError("Templates used by synchronized events cannot be deleted; deactivate them instead.")
    db.delete(row)
    db.commit()
    return True


