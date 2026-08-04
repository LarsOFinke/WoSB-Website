#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


_BACKUP_NAME_RE = re.compile(r"^rbf-postgres-[A-Za-z0-9T-]+\.dump$")
_FILES_BACKUP_NAME_RE = re.compile(r"^rbf-files-[A-Za-z0-9T-]+\.tar\.gz$")
_BACKUP_ID_RE = re.compile(r"^[a-f0-9]{64}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_MAX_CATALOG_ENTRIES = 200
_MAX_CHECKSUM_BYTES = 4096
_MAX_METADATA_BYTES = 32 * 1024


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
    restore_metadata_verified: bool = False
    encryption_keys_compatible: bool | None = None
    flyway_version: str | None = None
    backup_consistency: str = "unrecorded"
    production_consistent: bool = False
    backup_set_verified: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "checksum_verified": True,
            "restore_metadata_verified": self.restore_metadata_verified,
            "encryption_keys_compatible": self.encryption_keys_compatible,
            "flyway_version": self.flyway_version,
            "backup_consistency": self.backup_consistency,
            "production_consistent": self.production_consistent,
            "backup_set_verified": self.backup_set_verified,
        }


@dataclass(frozen=True)
class LocalFilesBackupRecord:
    backup_id: str
    filename: str
    path: Path
    size_bytes: int
    sha256: str
    created_at: str
    components: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "checksum_verified": True,
            "components": list(self.components),
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




def _read_env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized = value.strip()
        if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
            normalized = normalized[1:-1]
        values[key.strip()] = normalized
    return values


def _fingerprint_key(value: str) -> str | None:
    import base64

    try:
        decoded = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, ValueError):
        return None
    if len(decoded) != 32:
        return None
    return hashlib.sha256(decoded).hexdigest()


def _current_key_fingerprints(infra_dir: Path) -> set[str]:
    import base64

    values = _read_env_values(infra_dir / ".env")
    fingerprints: set[str] = set()
    for key in (item.strip() for item in values.get("WEBHOOK_ENCRYPTION_KEYS", "").split(",")):
        if fingerprint := _fingerprint_key(key):
            fingerprints.add(fingerprint)
    database_url = values.get("DATABASE_URL", "")
    if database_url:
        derived = base64.urlsafe_b64encode(
            hashlib.sha256(
                f"royal-blackwater-fleet:webhooks:v1:{database_url}".encode("utf-8")
            ).digest()
        ).decode("ascii")
        if fingerprint := _fingerprint_key(derived):
            fingerprints.add(fingerprint)
    return fingerprints


def _read_restore_metadata(path: Path, backup: Path, backup_sha256: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    checksum_path = path.with_name(f"{path.name}.sha256")
    if path.is_symlink() or checksum_path.is_symlink():
        raise LocalBackupError("Symlinked restore metadata is not accepted.")
    expected_metadata_sha = _expected_checksum(checksum_path, path.name)
    descriptor, before = _open_regular_nofollow(path)
    try:
        if before.st_size > _MAX_METADATA_BYTES:
            raise LocalBackupError("Restore metadata is unexpectedly large.")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read(_MAX_METADATA_BYTES + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if len(raw) > _MAX_METADATA_BYTES or _changed(before, after):
        raise LocalBackupError("Restore metadata changed while it was read.")
    actual_metadata_sha = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(expected_metadata_sha, actual_metadata_sha):
        raise LocalBackupError("Restore metadata checksum mismatch.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalBackupError("Restore metadata is invalid.") from exc
    if not isinstance(payload, dict) or int(payload.get("schema_version", -1)) not in {1, 2}:
        raise LocalBackupError("Unsupported restore metadata.")
    backup_data = payload.get("backup")
    if not isinstance(backup_data, dict):
        raise LocalBackupError("Restore metadata has no backup record.")
    if backup_data.get("filename") != backup.name:
        raise LocalBackupError("Restore metadata filename mismatch.")
    if int(backup_data.get("size_bytes", -1)) != backup.stat().st_size:
        raise LocalBackupError("Restore metadata size mismatch.")
    if not hmac.compare_digest(str(backup_data.get("sha256") or ""), backup_sha256):
        raise LocalBackupError("Restore metadata checksum mismatch.")
    return payload


def _verified_backup_set_members(infra_dir: Path) -> set[Path]:
    module_name = "rbf_backup_set_manifest"
    module = sys.modules.get(module_name)
    if module is None:
        script = Path(__file__).with_name("backup_set_manifest.py")
        spec = importlib.util.spec_from_file_location(module_name, script)
        if spec is None or spec.loader is None:
            raise LocalBackupError("Backup-set validator could not be loaded.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    validate_manifest = module.validate_manifest

    result: set[Path] = set()
    sets_dir = infra_dir / "data/backups/sets"
    if not sets_dir.is_dir():
        return result
    for manifest in sets_dir.glob("rbf-backup-set-*.json"):
        try:
            payload = validate_manifest(infra_dir, manifest)
            artifacts = payload.get("artifacts")
            postgres = artifacts.get("postgres") if isinstance(artifacts, dict) else None
            if isinstance(postgres, dict):
                result.add((infra_dir / str(postgres.get("path") or "")).resolve())
        except (RuntimeError, OSError, ValueError, json.JSONDecodeError):
            continue
    return result


def _record_for(path: Path, infra_dir: Path, verified_set_members: set[Path]) -> LocalBackupRecord:
    if not _BACKUP_NAME_RE.fullmatch(path.name):
        raise LocalBackupError("Unsupported PostgreSQL backup filename.")
    checksum_path = path.with_name(f"{path.name}.sha256")
    if path.is_symlink() or checksum_path.is_symlink():
        raise LocalBackupError("Symlinked backup entries are not accepted.")
    expected = _expected_checksum(checksum_path, path.name)
    actual, metadata = _hash_file(path)
    if not hmac.compare_digest(expected, actual):
        raise LocalBackupError(f"Backup checksum mismatch: {path.name}")
    restore_metadata = _read_restore_metadata(
        path.with_name(f"{path.name}.restore.json"), path, actual
    )
    metadata_verified = restore_metadata is not None
    compatible: bool | None = None
    flyway_version: str | None = None
    consistency = "unrecorded"
    production_consistent = False
    if restore_metadata is not None:
        security = restore_metadata.get("security")
        backup_fingerprints = {
            str(value)
            for value in (security.get("secret_key_fingerprints", []) if isinstance(security, dict) else [])
            if re.fullmatch(r"[a-f0-9]{64}", str(value))
        }
        current_fingerprints = _current_key_fingerprints(infra_dir)
        compatible = bool(backup_fingerprints & current_fingerprints) if backup_fingerprints else None
        application = restore_metadata.get("application")
        if isinstance(application, dict):
            flyway_version = str(application.get("flyway_version") or "") or None
        backup = restore_metadata.get("backup")
        if isinstance(backup, dict):
            consistency = str(backup.get("consistency") or "unrecorded")
            production_consistent = consistency in {"application-quiesced", "no-running-api"}

    identifier = hashlib.sha256(
        f"rbf-local-backup-v2\0{path.name}\0{metadata.st_size}\0{actual}".encode("utf-8")
    ).hexdigest()
    created_at = datetime.fromtimestamp(metadata.st_mtime, tz=timezone.utc).isoformat()
    return LocalBackupRecord(
        backup_id=identifier,
        filename=path.name,
        path=path,
        size_bytes=metadata.st_size,
        sha256=actual,
        created_at=created_at,
        restore_metadata_verified=metadata_verified,
        encryption_keys_compatible=compatible,
        flyway_version=flyway_version,
        backup_consistency=consistency,
        production_consistent=production_consistent,
        backup_set_verified=path.resolve() in verified_set_members,
    )


def scan_local_postgres_backups(infra_dir: Path) -> tuple[list[LocalBackupRecord], int]:
    root = (infra_dir / "data/backups/postgres").resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    verified_set_members = _verified_backup_set_members(infra_dir)
    records: list[LocalBackupRecord] = []
    skipped = 0
    try:
        candidates = list(root.iterdir())
    except OSError as exc:
        raise LocalBackupError(
            "The protected PostgreSQL backup directory could not be scanned."
        ) from exc
    for path in candidates:
        if path.name.endswith((".sha256", ".restore.json")) or path.name.startswith("."):
            continue
        try:
            if path.parent.resolve() != root:
                raise LocalBackupError("Backup path escaped the protected directory.")
            records.append(_record_for(path, infra_dir, verified_set_members))
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


def _files_record_for(path: Path) -> LocalFilesBackupRecord:
    if not _FILES_BACKUP_NAME_RE.fullmatch(path.name) or path.is_symlink():
        raise LocalBackupError("Unsupported files backup entry.")
    checksum_path = path.with_name(f"{path.name}.sha256")
    if checksum_path.is_symlink():
        raise LocalBackupError("Symlinked files-backup checksum is not accepted.")
    expected = _expected_checksum(checksum_path, path.name)
    actual, metadata = _hash_file(path)
    if not hmac.compare_digest(expected, actual):
        raise LocalBackupError(f"Files backup checksum mismatch: {path.name}")
    import tarfile

    components: set[str] = set()
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if (
                not parts
                or Path(member.name).is_absolute()
                or ".." in parts
                or parts[0] not in {"uploads", "certs", "letsencrypt", "uptime-kuma"}
                or not (member.isdir() or member.isfile())
            ):
                raise LocalBackupError(f"Unsafe files backup entry: {member.name}")
            components.add(parts[0])
    identifier = hashlib.sha256(
        f"rbf-local-files-v1\0{path.name}\0{metadata.st_size}\0{actual}".encode("utf-8")
    ).hexdigest()
    return LocalFilesBackupRecord(
        backup_id=identifier,
        filename=path.name,
        path=path,
        size_bytes=metadata.st_size,
        sha256=actual,
        created_at=datetime.fromtimestamp(metadata.st_mtime, tz=timezone.utc).isoformat(),
        components=tuple(sorted(components)),
    )


def scan_local_files_backups(infra_dir: Path) -> tuple[list[LocalFilesBackupRecord], int]:
    root = (infra_dir / "data/backups/files").resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    records: list[LocalFilesBackupRecord] = []
    skipped = 0
    for path in root.iterdir():
        if path.name.endswith(".sha256") or path.name.startswith("."):
            continue
        try:
            records.append(_files_record_for(path))
        except (LocalBackupError, OSError, ValueError):
            skipped += 1
    records.sort(key=lambda item: (item.created_at, item.filename), reverse=True)
    if len(records) > _MAX_CATALOG_ENTRIES:
        skipped += len(records) - _MAX_CATALOG_ENTRIES
        records = records[:_MAX_CATALOG_ENTRIES]
    return records, skipped


def resolve_local_files_backup(infra_dir: Path, backup_id: str) -> LocalFilesBackupRecord:
    normalized = str(backup_id or "").strip().lower()
    if not _BACKUP_ID_RE.fullmatch(normalized):
        raise LocalBackupError("Invalid files backup selection.")
    records, _ = scan_local_files_backups(infra_dir)
    for record in records:
        if hmac.compare_digest(record.backup_id, normalized):
            return record
    raise LocalBackupError("The selected files backup is no longer present in the verified host catalog.")


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
