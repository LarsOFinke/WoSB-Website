from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.builds.models.build import Build
from app.modules.builds.models.build_role import BuildRole
from app.modules.builds.schemas.build_role import BuildRoleCreate, BuildRoleUpdate


DEFAULT_BUILD_ROLES: tuple[dict[str, object], ...] = (
    {
        "slug": "balanced",
        "label": "Balanced",
        "description": "General-purpose build with no single dominant specialization.",
        "sort_order": 10,
    },
    {
        "slug": "boarding",
        "label": "Boarding",
        "description": "Build focused on boarding pressure and close-range crew combat.",
        "sort_order": 20,
    },
    {
        "slug": "gunnery",
        "label": "Gunnery",
        "description": "Build focused on weapon performance and ranged damage.",
        "sort_order": 30,
    },
    {
        "slug": "defensive",
        "label": "Defensive",
        "description": "Build focused on survivability, sustain and damage mitigation.",
        "sort_order": 40,
    },
)


class BuildRoleError(ValueError):
    pass


def ensure_default_build_roles(db: Session) -> None:
    """Initialize the role catalog once without undoing moderator CRUD changes."""

    if int(db.scalar(select(func.count()).select_from(BuildRole)) or 0) > 0:
        return
    db.add_all(BuildRole(**payload) for payload in DEFAULT_BUILD_ROLES)
    db.flush()


def list_build_roles(db: Session) -> list[BuildRole]:
    ensure_default_build_roles(db)
    return list(
        db.scalars(
            select(BuildRole).order_by(BuildRole.sort_order, func.lower(BuildRole.label), BuildRole.slug)
        ).all()
    )


def get_build_role(db: Session, slug: str) -> BuildRole | None:
    ensure_default_build_roles(db)
    return db.get(BuildRole, slug.strip().lower())


def require_build_role(db: Session, slug: str) -> BuildRole:
    role = get_build_role(db, slug)
    if role is None:
        raise BuildRoleError("The selected build role does not exist.")
    return role


def create_build_role(db: Session, payload: BuildRoleCreate) -> BuildRole:
    ensure_default_build_roles(db)
    if db.get(BuildRole, payload.slug) is not None:
        raise BuildRoleError("A build role with this slug already exists.")
    role = BuildRole(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_build_role(db: Session, slug: str, payload: BuildRoleUpdate) -> BuildRole:
    role = get_build_role(db, slug)
    if role is None:
        raise BuildRoleError("Build role not found.")
    for field_name, value in payload.model_dump().items():
        setattr(role, field_name, value)
    db.commit()
    db.refresh(role)
    return role


def delete_build_role(db: Session, slug: str) -> None:
    role = get_build_role(db, slug)
    if role is None:
        raise BuildRoleError("Build role not found.")
    usage_count = int(
        db.scalar(select(func.count()).select_from(Build).where(Build.build_type == role.slug)) or 0
    )
    if usage_count:
        raise BuildRoleError(
            f"Build role is still assigned to {usage_count} build(s). Reassign them before deleting it."
        )
    role_count = int(db.scalar(select(func.count()).select_from(BuildRole)) or 0)
    if role_count <= 1:
        raise BuildRoleError("At least one build role must remain available.")
    db.delete(role)
    db.commit()


def assign_build_role(db: Session, build_id: int, slug: str) -> Build | None:
    role = require_build_role(db, slug)
    build = db.get(Build, build_id)
    if build is None:
        return None
    build.build_type = role.slug
    db.commit()
    return build
