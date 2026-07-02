from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DbSession, OptionalCurrentUser
from app.schemas.build import BuildCreate, BuildOptionRead, BuildRead
from app.services import BuildNotFoundError, BuildOptionService, BuildService

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("", response_model=list[BuildRead])
def list_builds(db: DbSession, user: OptionalCurrentUser) -> list[BuildRead]:
    return BuildService(db).list_builds(viewer=user)


@router.get("/options/catalog", response_model=list[BuildOptionRead])
def list_build_options(
    db: DbSession,
    category: str | None = None,
    ship_id: int | None = None,
) -> list[BuildOptionRead]:
    return BuildOptionService(db).list_options(category=category, ship_id=ship_id)


@router.get("/{build_id}", response_model=BuildRead)
def get_build(build_id: int, db: DbSession, user: OptionalCurrentUser) -> BuildRead:
    try:
        return BuildService(db).get_build(build_id, viewer=user)
    except BuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=BuildRead, status_code=status.HTTP_201_CREATED)
def create_build(payload: BuildCreate, db: DbSession, user: CurrentUser) -> BuildRead:
    return BuildService(db).create_build(payload, author=user)
