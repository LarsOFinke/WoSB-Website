from datetime import datetime
import mimetypes
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.files.models.file_asset import StoredFile


class FileValidationError(ValueError):
    pass


ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "application/pdf",
    "text/plain",
}
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".mp4",
    ".webm",
    ".mov",
    ".pdf",
    ".txt",
}
def _mb(value: int) -> int:
    return value * 1024 * 1024


def _safe_extension(filename: str, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension(content_type or "") or ""
    guessed = guessed.lower()
    if guessed == ".jpe":
        guessed = ".jpg"
    if guessed in ALLOWED_EXTENSIONS:
        return guessed
    return ""


def _mime_type(upload: UploadFile, extension: str) -> str:
    content_type = (upload.content_type or "").split(";")[0].strip().lower()
    if content_type:
        return content_type
    guessed, _ = mimetypes.guess_type(f"file{extension}")
    return guessed or "application/octet-stream"


def _max_size_for_mime_type(mime_type: str) -> int:
    if mime_type.startswith("image/"):
        return _mb(settings.upload_image_limit_mb)
    if mime_type in {"application/pdf", "text/plain"}:
        return _mb(settings.upload_document_limit_mb)
    return _mb(settings.upload_video_limit_mb)


def _format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    unit = "B"
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            break
        value /= 1024
    return f"{value:.0f} {unit}" if value >= 10 or unit == "B" else f"{value:.1f} {unit}"


def upload_file(db: Session, upload: UploadFile, owner: User, usage_context: str = "general") -> StoredFile:
    extension = _safe_extension(upload.filename or "upload", upload.content_type)
    mime_type = _mime_type(upload, extension)
    if not extension or mime_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError("Unsupported file type. Allowed: GIF, MP4, JPEG, PNG, WebP, SVG, WebM, MOV, PDF and TXT.")

    max_size = _max_size_for_mime_type(mime_type)

    now = datetime.utcnow()
    folder = Path(settings.upload_dir) / f"{now:%Y}" / f"{now:%m}"
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    target = folder / stored_name

    size = 0
    with target.open("wb") as handle:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_size:
                handle.close()
                target.unlink(missing_ok=True)
                raise FileValidationError(f"File is too large. Maximum size for this type is {_format_size(max_size)}.")
            handle.write(chunk)

    if size <= 0:
        target.unlink(missing_ok=True)
        raise FileValidationError("Empty files cannot be uploaded.")

    relative_path = str(target.relative_to(Path(settings.upload_dir))).replace("\\", "/")
    db_file = StoredFile(
        owner_id=owner.id,
        original_name=upload.filename or stored_name,
        stored_name=stored_name,
        relative_path=relative_path,
        mime_type=mime_type,
        size_bytes=size,
        usage_context=(usage_context or "general")[:40],
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def list_files(db: Session, owner_id: int | None = None, usage_context: str | None = None) -> list[StoredFile]:
    statement = select(StoredFile).order_by(StoredFile.created_at.desc(), StoredFile.id.desc())
    if owner_id is not None:
        statement = statement.where(StoredFile.owner_id == owner_id)
    if usage_context:
        statement = statement.where(StoredFile.usage_context == usage_context)
    return list(db.scalars(statement).all())


def get_file(db: Session, file_id: int) -> StoredFile | None:
    return db.get(StoredFile, file_id)


def get_files_for_owner(db: Session, file_ids: list[int], owner: User) -> list[StoredFile]:
    if not file_ids:
        return []
    files = list(db.scalars(select(StoredFile).where(StoredFile.id.in_(file_ids))).all())
    found = {file.id: file for file in files}
    missing = [file_id for file_id in file_ids if file_id not in found]
    if missing:
        raise FileValidationError("One or more selected files do not exist.")
    for file in files:
        if file.owner_id not in (None, owner.id) and not owner.can_moderate:
            raise FileValidationError("One or more selected files are not owned by you.")
    return [found[file_id] for file_id in file_ids]


def delete_file(db: Session, file: StoredFile) -> None:
    path = Path(settings.upload_dir) / file.relative_path
    db.delete(file)
    db.commit()
    path.unlink(missing_ok=True)
    # Clean up empty month/year directories without touching non-empty folders.
    for parent in [path.parent, path.parent.parent]:
        try:
            parent.rmdir()
        except OSError:
            break
