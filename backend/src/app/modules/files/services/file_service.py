from __future__ import annotations

import mimetypes
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.modules.accounts.models.user import User
from app.modules.files.models.file_asset import StoredFile


class FileValidationError(ValueError):
    pass


EXTENSION_MIME_TYPES: dict[str, frozenset[str]] = {
    ".jpg": frozenset({"image/jpeg"}),
    ".jpeg": frozenset({"image/jpeg"}),
    ".png": frozenset({"image/png"}),
    ".gif": frozenset({"image/gif"}),
    ".webp": frozenset({"image/webp"}),
    ".mp4": frozenset({"video/mp4"}),
    ".webm": frozenset({"video/webm"}),
    ".mov": frozenset({"video/quicktime"}),
    ".pdf": frozenset({"application/pdf"}),
    ".txt": frozenset({"text/plain"}),
}
ALLOWED_EXTENSIONS = frozenset(EXTENSION_MIME_TYPES)
ALLOWED_MIME_TYPES = frozenset(
    mime_type for mime_types in EXTENSION_MIME_TYPES.values() for mime_type in mime_types
)


def _mb(value: int) -> int:
    return value * 1024 * 1024


def _safe_extension(filename: str, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return suffix
    guessed = (mimetypes.guess_extension(content_type or "") or "").lower()
    if guessed == ".jpe":
        guessed = ".jpg"
    return guessed if guessed in ALLOWED_EXTENSIONS else ""


def _declared_mime_type(upload: UploadFile, extension: str) -> str:
    content_type = (upload.content_type or "").split(";", 1)[0].strip().lower()
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


def _used_bytes(db: Session, *, owner_id: int | None = None) -> int:
    statement = select(func.coalesce(func.sum(StoredFile.size_bytes), 0))
    if owner_id is not None:
        statement = statement.where(StoredFile.owner_id == owner_id)
    return int(db.scalar(statement) or 0)


def _effective_upload_limit(db: Session, owner: User, mime_type: str, upload_root: Path) -> int:
    limits = [_max_size_for_mime_type(mime_type)]

    user_quota = _mb(settings.upload_per_user_total_mb)
    if user_quota > 0:
        limits.append(max(0, user_quota - _used_bytes(db, owner_id=owner.id)))

    global_quota = _mb(settings.upload_global_total_mb)
    if global_quota > 0:
        limits.append(max(0, global_quota - _used_bytes(db)))

    upload_root.mkdir(parents=True, exist_ok=True)
    free_after_reserve = max(
        0,
        shutil.disk_usage(upload_root).free - _mb(settings.upload_minimum_free_mb),
    )
    limits.append(free_after_reserve)

    maximum = min(limits)
    if maximum <= 0:
        raise FileValidationError(
            "Upload storage quota is exhausted or the server has reached its free-space reserve."
        )
    return maximum


def _detected_mime_type(path: Path, extension: str) -> str | None:
    with path.open("rb") as handle:
        header = handle.read(64)

    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    if header.startswith(b"%PDF-"):
        return "application/pdf"
    if header.startswith(b"\x1aE\xdf\xa3"):
        return "video/webm"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return "video/quicktime" if header[8:12] == b"qt  " else "video/mp4"
    if extension == ".txt":
        try:
            content = path.read_bytes()
            if b"\x00" in content:
                return None
            content.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return "text/plain"
    return None


def _validate_content(path: Path, extension: str, declared_mime_type: str) -> str:
    allowed_for_extension = EXTENSION_MIME_TYPES.get(extension, frozenset())
    if declared_mime_type not in allowed_for_extension:
        raise FileValidationError(
            "File extension and declared content type do not match an allowed upload format."
        )
    detected = _detected_mime_type(path, extension)
    if detected is None or detected not in allowed_for_extension:
        raise FileValidationError(
            "File contents do not match the declared extension and content type."
        )
    return detected


def upload_file(
    db: Session,
    upload: UploadFile,
    owner: User,
    usage_context: str = "general",
) -> StoredFile:
    extension = _safe_extension(upload.filename or "upload", upload.content_type)
    declared_mime_type = _declared_mime_type(upload, extension)
    if not extension or declared_mime_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            "Unsupported file type. Allowed: GIF, JPEG, PNG, WebP, MP4, WebM, MOV, PDF and UTF-8 TXT."
        )

    upload_root = Path(settings.upload_dir)
    maximum = _effective_upload_limit(db, owner, declared_mime_type, upload_root)

    now = utc_now()
    folder = upload_root / f"{now:%Y}" / f"{now:%m}"
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    target = folder / stored_name
    temporary = folder / f".{stored_name}.upload"

    size = 0
    try:
        with temporary.open("xb") as handle:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum:
                    raise FileValidationError(
                        f"File is too large or exceeds the remaining quota. Maximum available size is {_format_size(maximum)}."
                    )
                handle.write(chunk)

        if size <= 0:
            raise FileValidationError("Empty files cannot be uploaded.")

        mime_type = _validate_content(temporary, extension, declared_mime_type)
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        raise

    relative_path = str(target.relative_to(upload_root)).replace("\\", "/")
    db_file = StoredFile(
        owner_id=owner.id,
        original_name=(upload.filename or stored_name)[:255],
        stored_name=stored_name,
        relative_path=relative_path,
        mime_type=mime_type,
        size_bytes=size,
        usage_context=(usage_context or "general")[:40],
    )
    try:
        db.add(db_file)
        db.commit()
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
    db.refresh(db_file)
    return db_file


def list_files(
    db: Session,
    owner_id: int | None = None,
    usage_context: str | None = None,
) -> list[StoredFile]:
    statement = select(StoredFile).order_by(
        StoredFile.created_at.desc(), StoredFile.id.desc()
    )
    if owner_id is not None:
        statement = statement.where(StoredFile.owner_id == owner_id)
    if usage_context:
        statement = statement.where(StoredFile.usage_context == usage_context)
    return list(db.scalars(statement).all())


def get_file(db: Session, file_id: int) -> StoredFile | None:
    return db.get(StoredFile, file_id)


def get_file_by_relative_path(db: Session, relative_path: str) -> StoredFile | None:
    normalized = str(relative_path or "").replace("\\", "/").strip("/")
    if not normalized or any(part in {"", ".", ".."} for part in normalized.split("/")):
        return None
    return db.scalar(select(StoredFile).where(StoredFile.relative_path == normalized))


def resolve_stored_file_path(stored_file: StoredFile) -> Path | None:
    root = Path(settings.upload_dir).resolve()
    candidate = (root / stored_file.relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def get_files_for_owner(
    db: Session, file_ids: list[int], owner: User
) -> list[StoredFile]:
    if not file_ids:
        return []
    files = list(
        db.scalars(select(StoredFile).where(StoredFile.id.in_(file_ids))).all()
    )
    found = {file.id: file for file in files}
    missing = [file_id for file_id in file_ids if file_id not in found]
    if missing:
        raise FileValidationError("One or more selected files do not exist.")
    for file in files:
        if file.owner_id not in (None, owner.id) and not owner.can_moderate:
            raise FileValidationError("One or more selected files are not owned by you.")
    return [found[file_id] for file_id in file_ids]


def delete_file(db: Session, file: StoredFile) -> None:
    path = resolve_stored_file_path(file)
    db.delete(file)
    db.commit()
    if path is None:
        return
    path.unlink(missing_ok=True)
    for parent in [path.parent, path.parent.parent]:
        try:
            parent.rmdir()
        except OSError:
            break
