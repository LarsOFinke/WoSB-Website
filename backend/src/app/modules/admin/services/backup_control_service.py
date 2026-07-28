from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.backup_control import BackupControlStatus, BackupOperation


ACTIVE_STATES = {"queued", "running"}
RUNNING_STALE_AFTER = timedelta(minutes=5)
QUEUED_STALE_AFTER = timedelta(minutes=10)
STATUS_FILE = "backup-status.json"
REQUEST_FILE = "backup.request"
LOG_FILE = "backup.log"


class BackupControlError(RuntimeError):
    pass


def _request_dir() -> Path:
    path = Path(settings.control_request_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _status_dir() -> Path:
    return Path(settings.control_status_dir)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _log_tail(path: Path, limit: int = 120) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _active_status_is_stale(state: str, payload: dict[str, Any], *, request_exists: bool) -> bool:
    now = datetime.now(timezone.utc)
    if state == "running":
        reference = _parse_timestamp(payload.get("heartbeat_at")) or _parse_timestamp(
            payload.get("started_at")
        )
        return reference is None or now - reference > RUNNING_STALE_AFTER
    if state == "queued" and not request_exists:
        reference = _parse_timestamp(payload.get("requested_at"))
        return reference is None or now - reference > QUEUED_STALE_AFTER
    return False


def get_backup_control_status() -> BackupControlStatus:
    request_path = _request_dir() / REQUEST_FILE
    status_directory = _status_dir()
    payload = _read_json(status_directory / STATUS_FILE)
    request_payload = _read_json(request_path)
    state = str(payload.get("state") or "idle")

    if _active_status_is_stale(state, payload, request_exists=request_path.exists()):
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            **payload,
            "state": "failed",
            "message": "The previous backup operation stopped reporting a host-runner heartbeat.",
            "finished_at": now,
        }
        state = "failed"

    if request_payload and state not in ACTIVE_STATES:
        state = "queued"
        payload = {
            **payload,
            "state": state,
            "operation": request_payload.get("operation") or "backup",
            "message": "Backup request accepted and waiting for the host runner.",
            "requested_by": request_payload.get("requested_by"),
            "requested_at": request_payload.get("requested_at"),
            "started_at": None,
            "finished_at": None,
        }

    connection = payload.get("connection") if isinstance(payload.get("connection"), dict) else {}
    safe_payload = {
        **payload,
        "state": state,
        "connection": connection,
        "log_tail": _log_tail(status_directory / LOG_FILE),
        "request_available": not request_path.exists() and state not in ACTIVE_STATES,
    }
    return BackupControlStatus.model_validate(safe_payload)


def request_backup_operation(
    user: User,
    operation: BackupOperation,
    payload: dict[str, Any] | None = None,
) -> BackupControlStatus:
    directory = _request_dir()
    request_path = directory / REQUEST_FILE
    current = get_backup_control_status()
    if request_path.exists() or current.state in ACTIVE_STATES:
        raise BackupControlError("A backup operation is already queued or running.")

    now = datetime.now(timezone.utc).isoformat()
    request_payload: dict[str, Any] = {
        "requested_by": user.username,
        "requested_at": now,
        "operation": operation,
    }
    if payload:
        request_payload.update(payload)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{REQUEST_FILE}.",
        suffix=".tmp",
        dir=directory,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        try:
            os.link(temporary, request_path)
        except FileExistsError as exc:
            raise BackupControlError("A backup operation is already queued or running.") from exc
        request_path.chmod(0o600)
        directory_descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)
    return get_backup_control_status()
