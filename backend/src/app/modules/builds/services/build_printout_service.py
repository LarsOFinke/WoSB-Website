from __future__ import annotations

import hashlib
import os
import struct
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.modules.builds.models.build import Build

MAX_PRINTOUT_BYTES = 12 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class BuildPrintoutError(ValueError):
    pass


def printout_path(build_id: int) -> Path:
    return Path(settings.upload_dir) / "build-printouts" / f"build-{build_id}.png"


def public_printout_url(build_id: int) -> str:
    return f"/api/builds/{build_id}/printout"


def save_build_printout(db: Session, build: Build, upload: UploadFile) -> tuple[Build, bool]:
    if upload.content_type != "image/png":
        raise BuildPrintoutError("Build printouts must be PNG images.")

    target = printout_path(build.id)
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    header = b""
    temporary_path: Path | None = None
    previous_path = target.with_name(f".{target.name}.previous")
    try:
        with NamedTemporaryFile(
            prefix=f".build-{build.id}.", suffix=".upload", dir=target.parent, delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            while chunk := upload.file.read(1024 * 1024):
                if len(header) < 24:
                    header = (header + chunk)[:24]
                size += len(chunk)
                if size > MAX_PRINTOUT_BYTES:
                    raise BuildPrintoutError("Build printout exceeds the 12 MiB limit.")
                digest.update(chunk)
                handle.write(chunk)
        if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
            raise BuildPrintoutError("Build printout content is not a valid PNG image.")
        width, height = struct.unpack(">II", header[16:24])
        if not (1 <= width <= 10_000 and 1 <= height <= 20_000):
            raise BuildPrintoutError("Build printout dimensions are invalid.")

        checksum = digest.hexdigest()
        unchanged = build.printout_checksum == checksum and target.is_file()
        if unchanged:
            temporary_path.unlink(missing_ok=True)
        else:
            previous_path.unlink(missing_ok=True)
            if target.is_file():
                os.replace(target, previous_path)
            os.replace(temporary_path, target)
            temporary_path = None
            try:
                build.printout_checksum = checksum
                build.printout_size_bytes = size
                build.printout_updated_at = utc_now()
                db.add(build)
                db.commit()
                db.refresh(build)
            except Exception:
                db.rollback()
                target.unlink(missing_ok=True)
                if previous_path.is_file():
                    os.replace(previous_path, target)
                raise
            previous_path.unlink(missing_ok=True)
        return build, not unchanged
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        if not target.is_file() and previous_path.is_file():
            os.replace(previous_path, target)
        raise


def delete_build_printout(build_id: int) -> None:
    printout_path(build_id).unlink(missing_ok=True)
