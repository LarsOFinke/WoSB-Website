from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import PurePosixPath

from .config import Profile
from .sftp_client import (
    _MAX_SET_BYTES,
    _SET_RE,
    _remote_bytes,
    _remote_directory,
    _sidecar_digest,
    _verified_remote_file,
    connect,
)


@dataclass(frozen=True)
class BackupCatalogEntry:
    filename: str
    created_at: str
    reason: str
    status: str
    recoverable: bool
    artifact_types: tuple[str, ...]
    total_size_bytes: int
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _fallback_time(timestamp: object) -> str:
    try:
        return datetime.fromtimestamp(float(timestamp), timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _inspect_set(sftp, root: PurePosixPath, attribute, by_name: dict[str, object]):
    filename = str(attribute.filename)
    created_at = _fallback_time(getattr(attribute, "st_mtime", None))
    reason = "unknown"
    try:
        data = _verified_remote_file(sftp, root, filename, limit=_MAX_SET_BYTES)
        payload = json.loads(data.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise RuntimeError("unsupported manifest")
        created_at = str(payload.get("created_at") or created_at)
        reason = str(payload.get("reason") or reason)
        if payload.get("committed") is not True:
            raise RuntimeError("set is not committed")
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts:
            raise RuntimeError("manifest contains no artifacts")
        total_size = 0
        recoverable = False
        for artifact_type, record in artifacts.items():
            if not isinstance(record, dict):
                raise RuntimeError(f"invalid artifact record: {artifact_type}")
            artifact_name = str(record.get("filename") or "")
            if PurePosixPath(artifact_name).name != artifact_name:
                raise RuntimeError(f"unsafe artifact filename: {artifact_type}")
            if artifact_name not in by_name or f"{artifact_name}.sha256" not in by_name:
                raise RuntimeError(f"missing artifact or checksum: {artifact_type}")
            expected_size = int(record.get("size_bytes", -1))
            actual_size = int(getattr(by_name[artifact_name], "st_size", -2))
            if expected_size < 0 or actual_size != expected_size:
                raise RuntimeError(f"artifact size mismatch: {artifact_type}")
            sidecar = _remote_bytes(
                sftp, root / f"{artifact_name}.sha256", limit=4096
            )
            if _sidecar_digest(sidecar, artifact_name) != record.get("sha256"):
                raise RuntimeError(f"artifact checksum binding mismatch: {artifact_type}")
            total_size += actual_size
        verification = artifacts.get("verification")
        if isinstance(verification, dict):
            report_name = str(verification.get("filename") or "")
            report = json.loads(
                _verified_remote_file(sftp, root, report_name, limit=128 * 1024).decode(
                    "utf-8"
                )
            )
            recoverable = bool(
                isinstance(report, dict)
                and report.get("status") == "passed"
                and report.get("recoverable") is True
            )
            if not recoverable:
                raise RuntimeError("recovery preflight did not pass")
        return BackupCatalogEntry(
            filename=filename,
            created_at=created_at,
            reason=reason,
            status="successful",
            recoverable=recoverable,
            artifact_types=tuple(sorted(str(name) for name in artifacts)),
            total_size_bytes=total_size,
            detail="Committed backup set verified.",
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        RuntimeError,
    ) as exc:
        return BackupCatalogEntry(
            filename=filename,
            created_at=created_at,
            reason=reason,
            status="invalid",
            recoverable=False,
            artifact_types=(),
            total_size_bytes=0,
            detail=str(exc),
        )


def remote_backup_catalog(sftp, remote_directory: str) -> list[BackupCatalogEntry]:
    root = PurePosixPath(_remote_directory(remote_directory))
    attributes = sftp.listdir_attr(root.as_posix())
    by_name = {str(item.filename): item for item in attributes}
    entries = [
        _inspect_set(sftp, root, item, by_name)
        for item in attributes
        if _SET_RE.fullmatch(str(item.filename))
    ]
    return sorted(entries, key=lambda entry: (entry.created_at, entry.filename), reverse=True)


def fetch_backup_catalog(
    profile: Profile, *, password: str = ""
) -> list[BackupCatalogEntry]:
    profile = profile.normalized()
    profile.validate(require_fingerprint=True)
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            return remote_backup_catalog(sftp, profile.remote_directory)
        finally:
            sftp.close()
    finally:
        client.close()


__all__ = ["BackupCatalogEntry", "fetch_backup_catalog", "remote_backup_catalog"]
