from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SystemUpdateInternalStatus:
    state: str
    operation: str
    message: str
    requested_by: str | None
    requested_at: str | None
    started_at: str | None
    heartbeat_at: str | None
    finished_at: str | None
    commit_before: str | None
    commit_after: str | None
    request_available: bool


def _public_message(state: str, operation: str) -> str:
    if operation == "restart":
        return {
            "idle": "No server restart has been requested yet.",
            "queued": "A server restart is queued for the host runner.",
            "running": "The application server is restarting.",
            "succeeded": "The application server restarted successfully.",
            "failed": "The server restart failed. Review the configured webhook or host logs.",
        }.get(state, "Server restart status is available.")
    return {
        "idle": "No update has been requested yet.",
        "queued": "An update is queued for the host runner.",
        "running": "The update is currently running.",
        "succeeded": "The update completed successfully.",
        "failed": "The update failed. Review the configured webhook or host logs.",
    }.get(state, "Update status is available.")


def _read_system_update_status() -> SystemUpdateInternalStatus:
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
        operation = str(payload.get("operation") or "update")
        payload = {
            **payload,
            "state": state,
            "message": (
                f"The previous {operation} operation no longer reports an active host-runner heartbeat. "
                "It is treated as interrupted and a new server operation may be requested."
            ),
            "finished_at": now.isoformat(),
        }

    # The API cannot write the root-owned status directory. Until the host runner
    # claims the request, synthesize a queued state from the inbox payload.
    if request_payload and state not in ACTIVE_STATES:
        state = "queued"
        requested_operation = str(request_payload.get("operation") or "update")
        payload = {
            **payload,
            "operation": requested_operation,
            "message": f"{requested_operation} request accepted and waiting for the host runner.",
            "requested_by": request_payload.get("requested_by"),
            "requested_at": request_payload.get("requested_at"),
            "started_at": None,
            "finished_at": None,
        }

    message = str(payload.get("message") or "No update has been requested yet.")
    return SystemUpdateInternalStatus(
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
        request_available=not request_path.exists() and state not in ACTIVE_STATES,
    )


def get_system_update_internal_status() -> SystemUpdateInternalStatus:
    return _read_system_update_status()


def get_system_update_status() -> SystemUpdateStatus:
    status = _read_system_update_status()
    return SystemUpdateStatus(
        state=status.state,
        operation=status.operation,
        message=_public_message(status.state, status.operation),
        requested_at=status.requested_at,
        started_at=status.started_at,
        finished_at=status.finished_at,
        request_available=status.request_available,
    )


def request_system_update(
    user: User, operation: SystemUpdateOperation = "update"
) -> SystemUpdateStatus:
    directory = _request_dir()
    request_path = directory / REQUEST_FILE
    current = get_system_update_status()
    if request_path.exists() or current.state in ACTIVE_STATES:
        raise SystemUpdateError("A server operation is already queued or running.")

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
