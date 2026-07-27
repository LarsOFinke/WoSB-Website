from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.files.models.file_asset import StoredFile
from app.modules.files.services.file_service import (
    get_file,
    get_file_by_relative_path,
    resolve_stored_file_path,
)

PUBLIC_FILE_USAGE_CONTEXTS = frozenset({"forum", "guide", "master-data"})


def _require_file_access(stored_file: StoredFile, current_user: User | None) -> None:
    if stored_file.usage_context in PUBLIC_FILE_USAGE_CONTEXTS:
        return
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required.")
    if stored_file.owner_id == current_user.id or current_user.can_moderate:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="File access denied.")


def _file_response(stored_file: StoredFile, current_user: User | None) -> FileResponse:
    _require_file_access(stored_file, current_user)
    path = resolve_stored_file_path(stored_file)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return FileResponse(
        path,
        media_type=stored_file.mime_type,
        filename=stored_file.original_name,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


router = APIRouter(tags=["files"])
legacy_router = APIRouter(prefix="/uploads", include_in_schema=False)


@router.get("/{file_id}/content", response_class=FileResponse)
def get_file_content(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> FileResponse:
    stored_file = get_file(db, file_id)
    if stored_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return _file_response(stored_file, current_user)


@legacy_router.get("/{relative_path:path}", response_class=FileResponse)
def get_legacy_file_content(
    relative_path: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> FileResponse:
    stored_file = get_file_by_relative_path(db, relative_path)
    if stored_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return _file_response(stored_file, current_user)
