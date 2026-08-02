from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.build_options_catalog import BuildOptionsCatalog
from app.modules.builds.schemas.build_read import BuildRead
from app.modules.builds.schemas.build_summary import BuildPage
from app.modules.builds.schemas.build_role import BuildRoleRead
from app.modules.builds.schemas.build_vote import BuildVoteState
from app.modules.builds.schemas.build_update import BuildUpdate
from app.modules.builds.services.build_option_service import list_build_options
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope
from app.modules.builds.services.build_role_service import list_build_roles
from app.modules.builds.services.build_vote_service import add_build_upvote, remove_build_upvote
from app.modules.builds.services.build_service import (
    BuildValidationError,
    create_build,
    delete_user_build,
    get_build,
    list_build_page,
    list_user_build_page,
    update_user_build,
)

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("", response_model=BuildPage)
def get_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    classification: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildPage:
    return list_build_page(
        db,
        search=search,
        build_type=build_type,
        classification=classification,
        viewer_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=BuildRead, status_code=status.HTTP_201_CREATED)
def post_build(
    build: BuildCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildRead:
    try:
        created = create_build(db, build, owner_id=current_user.id)
    except BuildValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build",
        entity_id=created.id,
        action="create",
        summary=f"Build “{created.build_name}” created.",
        changed_fields=list(build.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(
        background_tasks,
        queue_webhook_event_safely(
            db,
            event_type="build.created",
            resource_type="build",
            resource_id=created.id,
            resource_url=f"/builds/{created.id}",
            actor=current_user,
            data=BuildRead.model_validate(created),
            **webhook_event_scope(db, use_primary_fleet=True),
        ),
    )
    return created


@router.get("/options", response_model=BuildOptionsCatalog)
def get_build_options(
    ship_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> BuildOptionsCatalog:
    return list_build_options(db, ship_id=ship_id)


@router.get("/roles", response_model=list[BuildRoleRead])
def get_build_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[BuildRoleRead]:
    return list_build_roles(db)


@router.post("/{build_id}/upvote", response_model=BuildVoteState)
def post_build_upvote(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildVoteState:
    state = add_build_upvote(db, build_id, current_user.id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    return state


@router.delete("/{build_id}/upvote", response_model=BuildVoteState)
def delete_build_upvote(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildVoteState:
    state = remove_build_upvote(db, build_id, current_user.id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    return state


@router.get("/mine", response_model=BuildPage)
def get_my_builds(
    search: str | None = Query(default=None, max_length=120),
    build_type: str | None = Query(default=None, max_length=32),
    classification: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildPage:
    return list_user_build_page(
        db,
        current_user.id,
        search=search,
        build_type=build_type,
        classification=classification,
        limit=limit,
        offset=offset,
    )


@router.put("/mine/{build_id}", response_model=BuildRead)
def put_my_build(
    build_id: int,
    build: BuildUpdate,
    background_tasks: BackgroundTasks,
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
        db,
        actor=current_user,
        entity_type="build",
        entity_id=build_id,
        action="update",
        summary=f"Build “{updated.build_name}” updated.",
        changed_fields=list(build.model_dump(exclude_unset=True).keys()),
    )
    schedule_webhook_deliveries(
        background_tasks,
        queue_webhook_event_safely(
            db,
            event_type="build.updated",
            resource_type="build",
            resource_id=build_id,
            resource_url=f"/builds/{build_id}",
            actor=current_user,
            data=BuildRead.model_validate(updated),
            **webhook_event_scope(db, use_primary_fleet=True),
        ),
    )
    return updated


@router.delete("/mine/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_build(
    build_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    existing = get_build(db, build_id)
    deleted = delete_user_build(db, build_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="build",
        entity_id=build_id,
        action="delete",
        summary=f"Build “{getattr(existing, 'build_name', build_id)}” deleted.",
    )
    schedule_webhook_deliveries(
        background_tasks,
        queue_webhook_event_safely(
            db,
            event_type="build.removed",
            resource_type="build",
            resource_id=build_id,
            resource_url="/builds",
            actor=current_user,
            data={"id": build_id, "build_name": getattr(existing, "build_name", str(build_id))},
            **webhook_event_scope(db, use_primary_fleet=True),
        ),
    )


@router.get("/{build_id}", response_model=BuildRead)
def get_build_detail(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildRead:
    build = get_build(db, build_id, viewer_id=current_user.id)
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    return build
