from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.system_update import SystemUpdateOperation, SystemUpdateStatus


ACTIVE_STATES = {"queued", "running"}
RUNNING_STALE_AFTER = timedelta(minutes=3)
QUEUED_STALE_AFTER = timedelta(minutes=10)
STATUS_FILE = "update-status.json"
REQUEST_FILE = "update.request"
LOG_FILE = "update.log"


class SystemUpdateError(RuntimeError):
    pass


def _request_dir() -> Path:
    path = Path(settings.control_request_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _status_dir() -> Path:
    return Path(settings.control_status_dir)


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


def _active_status_is_stale(
    state: str,
    payload: dict,
    *,
    request_exists: bool,
    now: datetime,
) -> bool:
    if state == "running":
        reference = _parse_timestamp(payload.get("heartbeat_at")) or _parse_timestamp(
            payload.get("started_at")
        )
        return reference is None or now - reference > RUNNING_STALE_AFTER
    if state == "queued" and not request_exists:
        reference = _parse_timestamp(payload.get("requested_at"))
        return reference is None or now - reference > QUEUED_STALE_AFTER
    return False


def get_system_update_status() -> SystemUpdateStatus:
    request_path = _request_dir() / REQUEST_FILE
    status_directory = _status_dir()
    payload = _read_json(status_directory / STATUS_FILE)
    request_payload = _read_json(request_path)
    state = str(payload.get("state") or "idle")
    now = datetime.now(timezone.utc)

    if _active_status_is_stale(
        state,
        payload,
        request_exists=request_path.exists(),
        now=now,
    ):
        state = "failed"
        payload = {
            **payload,
            "state": state,
            "message": (
                "The previous update no longer reports an active host-runner heartbeat. "
                "It is treated as interrupted and a new update may be requested."
            ),
            "finished_at": now.isoformat(),
        }

    # The API cannot write the root-owned status directory. Until the host runner
    # claims the request, synthesize a queued state from the inbox payload.
    if request_payload and state not in ACTIVE_STATES:
        state = "queued"
        payload = {
            **payload,
            "operation": request_payload.get("operation") or "update",
            "message": "Update request accepted and waiting for the host runner.",
            "requested_by": request_payload.get("requested_by"),
            "requested_at": request_payload.get("requested_at"),
            "started_at": None,
            "finished_at": None,
        }

    message = str(payload.get("message") or "No update has been requested yet.")
    return SystemUpdateStatus(
        state=state,
        operation=str(payload.get("operation") or "update"),
        message=message,
        requested_by=payload.get("requested_by"),
        requested_at=payload.get("requested_at"),
        started_at=payload.get("started_at"),
        heartbeat_at=payload.get("heartbeat_at"),
        finished_at=payload.get("finished_at"),
        commit_before=payload.get("commit_before"),
        commit_after=payload.get("commit_after"),
        log_tail=_log_tail(status_directory / LOG_FILE),
        request_available=not request_path.exists() and state not in ACTIVE_STATES,
    )


def request_system_update(
    user: User, operation: SystemUpdateOperation = "update"
) -> SystemUpdateStatus:
    directory = _request_dir()
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
    request_tmp = directory / f".{REQUEST_FILE}.{os.getpid()}.tmp"
    request_tmp.write_text(
        json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    request_tmp.chmod(0o600)
    os.replace(request_tmp, request_path)
    request_path.chmod(0o600)
    return get_system_update_status()
