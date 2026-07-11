from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.system_update import SystemUpdateOperation, SystemUpdateStatus


ACTIVE_STATES = {"queued", "running"}
STATUS_FILE = "update-status.json"
REQUEST_FILE = "update.request"
LOG_FILE = "update.log"


class SystemUpdateError(RuntimeError):
    pass


def _control_dir() -> Path:
    path = Path(settings.control_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path) -> dict:
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


def get_system_update_status() -> SystemUpdateStatus:
    directory = _control_dir()
    payload = _read_json(directory / STATUS_FILE)
    state = str(payload.get("state") or "idle")
    message = str(payload.get("message") or "No update has been requested yet.")
    return SystemUpdateStatus(
        state=state,
        operation=str(payload.get("operation") or "update"),
        message=message,
        requested_by=payload.get("requested_by"),
        requested_at=payload.get("requested_at"),
        started_at=payload.get("started_at"),
        finished_at=payload.get("finished_at"),
        commit_before=payload.get("commit_before"),
        commit_after=payload.get("commit_after"),
        log_tail=_log_tail(directory / LOG_FILE),
        request_available=not (directory / REQUEST_FILE).exists() and state not in ACTIVE_STATES,
    )


def request_system_update(
    user: User, operation: SystemUpdateOperation = "update"
) -> SystemUpdateStatus:
    directory = _control_dir()
    request_path = directory / REQUEST_FILE
    current = get_system_update_status()
    if request_path.exists() or current.state in ACTIVE_STATES:
        raise SystemUpdateError("A server update is already queued or running.")

    now = datetime.now(timezone.utc).isoformat()
    request_payload = {
        "requested_by": user.username,
        "requested_at": now,
        "operation": operation,
    }
    queued_status = {
        "state": "queued",
        "operation": operation,
        "message": "Update request accepted and waiting for the host runner.",
        "requested_by": user.username,
        "requested_at": now,
        "started_at": None,
        "finished_at": None,
        "commit_before": current.commit_after or current.commit_before,
        "commit_after": None,
    }

    status_tmp = directory / f".{STATUS_FILE}.tmp"
    request_tmp = directory / f".{REQUEST_FILE}.tmp"
    status_tmp.write_text(json.dumps(queued_status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    request_tmp.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(status_tmp, directory / STATUS_FILE)
    # Create the watched request file last so systemd cannot start before the
    # queued status is visible to the API.
    os.replace(request_tmp, request_path)
    return get_system_update_status()
