from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.outbound_webhook_delivery_service import (
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.webhook_event_scope import webhook_event_scope
from app.modules.builds.models.build import Build
from app.modules.builds.schemas.build_printout import BuildPrintoutRead
from app.modules.builds.services.build_printout_service import (
    BuildPrintoutError,
    printout_path,
    public_printout_url,
    save_build_printout,
)
from app.modules.builds.services.build_service import get_build

router = APIRouter(prefix="/builds", tags=["builds"])


@router.put("/{build_id}/printout", response_model=BuildPrintoutRead)
def put_build_printout(
    build_id: int,
    background_tasks: BackgroundTasks,
    notify_discord: bool = Query(default=False),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BuildPrintoutRead:
    build = get_build(db, build_id)
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found.")
    if build.owner_id != current_user.id and not current_user.can_moderate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Build printout access denied."
        )
    try:
        build, changed = save_build_printout(db, build, image)
    except BuildPrintoutError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    url = public_printout_url(build.id)
    if notify_discord:
        delivery_ids = queue_webhook_event_safely(
            db,
            event_type="build.printout.published",
            resource_type="build_printout",
            resource_id=build.id,
            resource_url=url,
            actor=current_user,
            data={
                "id": build.id,
                "build_name": build.build_name,
                "image_url": url,
                "checksum": build.printout_checksum,
                "changed": changed,
            },
            **webhook_event_scope(db, use_primary_fleet=True),
        )
        schedule_webhook_deliveries(background_tasks, delivery_ids)
    return BuildPrintoutRead(
        url=url,
        checksum=build.printout_checksum or "",
        size_bytes=build.printout_size_bytes or 0,
        updated_at=build.printout_updated_at or build.updated_at,
        changed=changed,
    )


@router.get("/{build_id}/printout", response_class=FileResponse)
def get_build_printout(build_id: int, db: Session = Depends(get_db)) -> FileResponse:
    build = db.get(Build, build_id)
    path = printout_path(build_id)
    if build is None or not build.printout_checksum or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Build printout not found."
        )
    return FileResponse(
        path,
        media_type="image/png",
        filename=f"build-{build_id}.png",
        content_disposition_type="inline",
        headers={
            "Cache-Control": "public, no-cache",
            "ETag": f'"{build.printout_checksum}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
