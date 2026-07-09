from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.db.session import get_db
from app.models import User
from app.schemas import FileRead
from app.services.file_service import FileValidationError, delete_file, get_file, list_files, upload_file

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[FileRead])
def get_files(
    usage_context: str | None = Query(default=None, max_length=40),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[FileRead]:
    return list_files(db, owner_id=current_user.id, usage_context=usage_context)


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
def post_file(
    file: UploadFile = File(...),
    usage_context: str = Query(default="general", max_length=40),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FileRead:
    try:
        return upload_file(db, file, owner=current_user, usage_context=usage_context)
    except FileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> None:
    file = get_file(db, file_id)
    if file is None or (file.owner_id != current_user.id and not current_user.can_moderate):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    delete_file(db, file)
