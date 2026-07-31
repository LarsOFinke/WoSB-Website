#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
from typing import Any


_BACKUP_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,139}\.sql(?:\.gz)?$")
_BACKUP_ID_RE = re.compile(r"^[a-f0-9]{64}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_MAX_CATALOG_ENTRIES = 200
_MAX_CHECKSUM_BYTES = 4096


class LocalBackupError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalBackupRecord:
    backup_id: str
    filename: str
    path: Path
    size_bytes: int
    sha256: str
    created_at: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "checksum_verified": True,
        }


def _open_regular_nofollow(path: Path) -> tuple[int, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LocalBackupError(f"Could not open protected backup file: {path.name}") from exc
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise LocalBackupError(f"Backup entry is not a regular file: {path.name}")
    return descriptor, metadata


def _read_small_text(path: Path) -> str:
    descriptor, before = _open_regular_nofollow(path)
    try:
        if before.st_size > _MAX_CHECKSUM_BYTES:
            raise LocalBackupError(f"Checksum file is unexpectedly large: {path.name}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(_MAX_CHECKSUM_BYTES + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if len(payload) > _MAX_CHECKSUM_BYTES or _changed(before, after):
        raise LocalBackupError(f"Checksum file changed while it was read: {path.name}")
    try:
        return payload.decode("ascii")
    except UnicodeDecodeError as exc:
        raise LocalBackupError(f"Checksum file is not ASCII: {path.name}") from exc


def _changed(before: os.stat_result, after: os.stat_result) -> bool:
    return (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    )


def _hash_file(path: Path) -> tuple[str, os.stat_result]:
    descriptor, before = _open_regular_nofollow(path)
    digest = hashlib.sha256()
    try:
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if _changed(before, after):
        raise LocalBackupError(f"Backup changed while it was verified: {path.name}")
    return digest.hexdigest(), before


def _expected_checksum(checksum_path: Path, filename: str) -> str:
    lines = [line.strip() for line in _read_small_text(checksum_path).splitlines() if line.strip()]
    if len(lines) != 1:
        raise LocalBackupError(
            f"Checksum file must contain exactly one entry: {checksum_path.name}"
        )
    fields = lines[0].split()
    digest = fields[0].lower() if fields else ""
    if not _SHA256_RE.fullmatch(digest):
        raise LocalBackupError(f"Checksum file has no valid SHA-256 digest: {checksum_path.name}")
    if len(fields) > 1:
        recorded_name = fields[-1].lstrip("*")
        if recorded_name != filename:
            raise LocalBackupError(f"Checksum filename does not match backup: {checksum_path.name}")
    return digest


def _record_for(path: Path) -> LocalBackupRecord:
    if not _BACKUP_NAME_RE.fullmatch(path.name):
        raise LocalBackupError("Unsupported PostgreSQL backup filename.")
    checksum_path = path.with_name(f"{path.name}.sha256")
    if path.is_symlink() or checksum_path.is_symlink():
        raise LocalBackupError("Symlinked backup entries are not accepted.")
    expected = _expected_checksum(checksum_path, path.name)
    actual, metadata = _hash_file(path)
    if not hmac.compare_digest(expected, actual):
        raise LocalBackupError(f"Backup checksum mismatch: {path.name}")
    identifier = hashlib.sha256(
        f"rbf-local-backup-v1\0{path.name}\0{metadata.st_size}\0{actual}".encode("utf-8")
    ).hexdigest()
    created_at = datetime.fromtimestamp(metadata.st_mtime, tz=timezone.utc).isoformat()
    return LocalBackupRecord(
        backup_id=identifier,
        filename=path.name,
        path=path,
        size_bytes=metadata.st_size,
        sha256=actual,
        created_at=created_at,
    )


def scan_local_postgres_backups(infra_dir: Path) -> tuple[list[LocalBackupRecord], int]:
    root = (infra_dir / "data/backups/postgres").resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    records: list[LocalBackupRecord] = []
    skipped = 0
    try:
        candidates = list(root.iterdir())
    except OSError as exc:
        raise LocalBackupError(
            "The protected PostgreSQL backup directory could not be scanned."
        ) from exc
    for path in candidates:
        if path.name.endswith(".sha256") or path.name.startswith("."):
            continue
        try:
            if path.parent.resolve() != root:
                raise LocalBackupError("Backup path escaped the protected directory.")
            records.append(_record_for(path))
        except (LocalBackupError, OSError):
            skipped += 1
    records.sort(key=lambda item: (item.created_at, item.filename), reverse=True)
    if len(records) > _MAX_CATALOG_ENTRIES:
        skipped += len(records) - _MAX_CATALOG_ENTRIES
        records = records[:_MAX_CATALOG_ENTRIES]
    return records, skipped


def resolve_local_postgres_backup(infra_dir: Path, backup_id: str) -> LocalBackupRecord:
    normalized = str(backup_id or "").strip().lower()
    if not _BACKUP_ID_RE.fullmatch(normalized):
        raise LocalBackupError("Invalid local backup selection.")
    records, _ = scan_local_postgres_backups(infra_dir)
    for record in records:
        if hmac.compare_digest(record.backup_id, normalized):
            return record
    raise LocalBackupError("The selected backup is no longer present in the verified host catalog.")


def consume_database_restore_approval(infra_dir: Path, token_sha256: str) -> None:
    normalized_hash = str(token_sha256 or "").strip().lower()
    approval_file = infra_dir / "data/control/secrets/database-restore-approval.json"
    if not _SHA256_RE.fullmatch(normalized_hash):
        approval_file.unlink(missing_ok=True)
        raise LocalBackupError("The one-time host approval token is invalid.")
    descriptor: int | None = None
    try:
        descriptor, metadata = _open_regular_nofollow(approval_file)
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read(8193)
        after = os.fstat(descriptor)
    except (OSError, LocalBackupError) as exc:
        approval_file.unlink(missing_ok=True)
        raise LocalBackupError(
            "No active one-time database-restore approval exists on the host."
        ) from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
    # Consume before validation so every attempt is single-use, including malformed or wrong tokens.
    approval_file.unlink(missing_ok=True)
    if metadata.st_size > 8192 or len(raw) > 8192 or _changed(metadata, after):
        raise LocalBackupError("The one-time database-restore approval is invalid.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalBackupError("The one-time database-restore approval is invalid.") from exc
    if not isinstance(payload, dict) or payload.get("purpose") != "database_restore":
        raise LocalBackupError("The one-time database-restore approval is invalid.")
    expires_at_raw = payload.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LocalBackupError(
            "The one-time database-restore approval has no valid expiry."
        ) from exc
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expires_at.astimezone(timezone.utc):
        raise LocalBackupError("The one-time database-restore approval has expired.")
    expected_hash = str(payload.get("token_sha256") or "").lower()
    if not _SHA256_RE.fullmatch(expected_hash) or not hmac.compare_digest(
        expected_hash, normalized_hash
    ):
        raise LocalBackupError("The one-time database-restore approval token was rejected.")

