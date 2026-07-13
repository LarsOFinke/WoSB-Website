from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.build_options_catalog import BuildOptionsCatalog
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.builds.schemas.build_update import BuildUpdate
from app.modules.builds.services.build_option_service import list_build_options
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.builds.services.build_service import (
    BuildValidationError,
    create_build,
    delete_user_build,
    get_build,
    list_builds,
    list_user_builds,
    update_user_build,
)

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("", response_model=list[BuildRead])
def get_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[BuildRead]:
    return list_builds(db, search=search, build_type=build_type)


@router.post("", response_model=BuildRead, status_code=status.HTTP_201_CREATED)
def post_build(
    build: BuildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildRead:
    try:
        created = create_build(db, build, owner_id=current_user.id)
    except BuildValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db, actor=current_user, entity_type="build", entity_id=created.id, action="create",
        summary=f'Build “{created.build_name}” created.',
        changed_fields=list(build.model_dump(exclude_unset=True).keys()),
    )
    return created


@router.get("/options", response_model=BuildOptionsCatalog)
def get_build_options(
    ship_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> BuildOptionsCatalog:
    return list_build_options(db, ship_id=ship_id)


@router.get("/mine", response_model=list[BuildRead])
def get_my_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[BuildRead]:
    return list_user_builds(db, current_user.id, search=search, build_type=build_type)


@router.put("/mine/{build_id}", response_model=BuildRead)
def put_my_build(
    build_id: int,
    build: BuildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildRead:
    try:
        updated = update_user_build(db, build_id, current_user.id, build)
    except BuildValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="build", entity_id=build_id, action="update",
        summary=f'Build “{updated.build_name}” updated.',
        changed_fields=list(build.model_dump(exclude_unset=True).keys()),
    )
    return updated


@router.delete("/mine/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = get_build(db, build_id)
    deleted = delete_user_build(db, build_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    record_audit_safely(
        db, actor=current_user, entity_type="build", entity_id=build_id, action="delete",
        summary=f'Build “{getattr(existing, "build_name", build_id)}” deleted.',
    )


@router.get("/{build_id}", response_model=BuildRead)
def get_build_detail(
    build_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> BuildRead:
    build = get_build(db, build_id)
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    return build
