from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.backup_control import BackupControlStatus, BackupOperation
from app.modules.admin.services.backup_control_repository import BackupControlRepository


ACTIVE_STATES = {"queued", "running"}
RUNNING_STALE_AFTER = timedelta(minutes=5)
QUEUED_STALE_AFTER = timedelta(minutes=10)
UtcClock = Callable[[], datetime]


class BackupControlStore(Protocol):
    def read_status(self) -> dict[str, Any]: ...

    def read_request(self) -> dict[str, Any]: ...

    def request_exists(self) -> bool: ...

    def publish_request(self, payload: dict[str, Any]) -> None: ...


class BackupControlError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BackupControlService:
    """Coordinates the API side of the asynchronous host-runner contract."""

    def __init__(
        self,
        repository: BackupControlStore,
        *,
        clock: UtcClock = _utc_now,
    ) -> None:
        self.repository = repository
        self.clock = clock

    @staticmethod
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
        self, state: str, payload: dict[str, Any], *, request_exists: bool
    ) -> bool:
        now = self.clock()
        if state == "running":
            reference = self._parse_timestamp(payload.get("heartbeat_at")) or self._parse_timestamp(
                payload.get("started_at")
            )
            return reference is None or now - reference > RUNNING_STALE_AFTER
        if state == "queued" and not request_exists:
            reference = self._parse_timestamp(payload.get("requested_at"))
            return reference is None or now - reference > QUEUED_STALE_AFTER
        return False

    def get_status(self) -> BackupControlStatus:
        payload = self.repository.read_status()
        request_payload = self.repository.read_request()
        request_exists = self.repository.request_exists()
        state = str(payload.get("state") or "idle")

        if self._active_status_is_stale(state, payload, request_exists=request_exists):
            payload = {
                **payload,
                "state": "failed",
                "message": "The previous backup operation stopped reporting a host-runner heartbeat.",
                "finished_at": self.clock().isoformat(),
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

        connection = (
            payload.get("connection") if isinstance(payload.get("connection"), dict) else {}
        )
        return BackupControlStatus.model_validate(
            {
                **payload,
                "state": state,
                "connection": connection,
                "request_available": not request_exists and state not in ACTIVE_STATES,
            }
        )

    def request_operation(
        self,
        user: User,
        operation: BackupOperation,
        payload: dict[str, Any] | None = None,
    ) -> BackupControlStatus:
        current = self.get_status()
        if self.repository.request_exists() or current.state in ACTIVE_STATES:
            raise BackupControlError("A backup operation is already queued or running.")

        request_payload: dict[str, Any] = {
            "requested_by": user.username,
            "requested_at": self.clock().isoformat(),
            "operation": operation,
        }
        if payload:
            request_payload.update(payload)
        try:
            self.repository.publish_request(request_payload)
        except FileExistsError as exc:
            raise BackupControlError("A backup operation is already queued or running.") from exc
        return self.get_status()


@lru_cache(maxsize=1)
def get_backup_control_service() -> BackupControlService:
    """Return one immutable-path service per API worker."""
    repository = BackupControlRepository(
        Path(settings.control_request_dir),
        Path(settings.control_status_dir),
    )
    return BackupControlService(repository)


# Stable functional facade for callers outside FastAPI and existing integrations.
def get_backup_control_status() -> BackupControlStatus:
    return get_backup_control_service().get_status()


def request_backup_operation(
    user: User,
    operation: BackupOperation,
    payload: dict[str, Any] | None = None,
) -> BackupControlStatus:
    return get_backup_control_service().request_operation(user, operation, payload)
