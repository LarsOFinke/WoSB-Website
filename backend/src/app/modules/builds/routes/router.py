from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.build_options_catalog import BuildOptionsCatalog
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.builds.services.build_option_service import list_build_options
from app.modules.builds.services.build_service import (
    BuildValidationError,
    create_build,
    delete_user_build,
    get_build,
    list_builds,
    list_user_builds,
)

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("", response_model=list[BuildRead])
def get_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
) -> list[BuildRead]:
    return list_builds(db, search=search, build_type=build_type)


@router.post("", response_model=BuildRead, status_code=status.HTTP_201_CREATED)
def post_build(
    build: BuildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildRead:
    try:
        return create_build(db, build, owner_id=current_user.id)
    except BuildValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/options", response_model=BuildOptionsCatalog)
def get_build_options(db: Session = Depends(get_db)) -> BuildOptionsCatalog:
    return list_build_options(db)


@router.get("/mine", response_model=list[BuildRead])
def get_my_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[BuildRead]:
    return list_user_builds(db, current_user.id, search=search, build_type=build_type)


@router.delete("/mine/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    deleted = delete_user_build(db, build_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")


@router.get("/{build_id}", response_model=BuildRead)
def get_build_detail(build_id: int, db: Session = Depends(get_db)) -> BuildRead:
    build = get_build(db, build_id)
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    return build
