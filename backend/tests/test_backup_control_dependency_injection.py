from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

from app.modules.admin.services.backup_control_service import BackupControlService


class MemoryBackupControlStore:
    def __init__(
        self,
        *,
        status: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
    ) -> None:
        self.status = status or {}
        self.request = request or {}
        self.published: list[dict[str, Any]] = []

    def read_status(self) -> dict[str, Any]:
        return self.status.copy()

    def read_request(self) -> dict[str, Any]:
        return self.request.copy()

    def request_exists(self) -> bool:
        return bool(self.request or self.published)

    def publish_request(self, payload: dict[str, Any]) -> None:
        self.published.append(payload.copy())
        self.request = payload.copy()


def test_injected_clock_makes_stale_runner_detection_deterministic() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    store = MemoryBackupControlStore(
        status={
            "state": "running",
            "started_at": (now - timedelta(minutes=6)).isoformat(),
        }
    )

    status = BackupControlService(store, clock=lambda: now).get_status()

    assert status.state == "failed"
    assert status.finished_at == now.isoformat()
    assert status.request_available is True


def test_injected_store_receives_normalized_operation_request() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    store = MemoryBackupControlStore()
    service = BackupControlService(store, clock=lambda: now)

    status = service.request_operation(
        SimpleNamespace(username="backup-admin"),  # type: ignore[arg-type]
        "discover",
        {"host": "backup.internal", "port": 22},
    )

    assert store.published == [
        {
            "requested_by": "backup-admin",
            "requested_at": now.isoformat(),
            "operation": "discover",
            "host": "backup.internal",
            "port": 22,
        }
    ]
    assert status.state == "queued"
