from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4


EVENT_PREFIX = "maintenance-event-"


@dataclass(frozen=True)
class MaintenanceEvent:
    event_id: str
    action: str
    reason: str
    message: str
    occurred_at: str
    started_at: str
    outcome: str | None = None


class MaintenanceEventOutbox:
    """Durable filesystem handoff from privileged host tools to the API."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def publish(
        self,
        *,
        action: str,
        reason: str,
        message: str,
        started_at: str,
        outcome: str | None = None,
    ) -> MaintenanceEvent:
        if action not in {"started", "ended"}:
            raise ValueError(f"Unsupported maintenance action: {action}")
        if outcome not in {None, "succeeded", "failed"}:
            raise ValueError(f"Unsupported maintenance outcome: {outcome}")
        event = MaintenanceEvent(
            event_id=uuid4().hex,
            action=action,
            reason=reason,
            message=" ".join(message.split())[:500],
            occurred_at=datetime.now(timezone.utc).isoformat(),
            started_at=started_at,
            outcome=outcome,
        )
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{EVENT_PREFIX}{event.event_id}.json"
        temporary = self.directory / f".{path.name}.{os.getpid()}.tmp"
        temporary.write_text(
            json.dumps(asdict(event), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        os.replace(temporary, path)
        path.chmod(0o600)
        return event

    def pending_paths(self) -> list[Path]:
        return sorted(self.directory.glob(f"{EVENT_PREFIX}*.json"))

    @staticmethod
    def read(path: Path) -> MaintenanceEvent:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return MaintenanceEvent(
            event_id=str(payload["event_id"]),
            action=str(payload["action"]),
            reason=str(payload["reason"]),
            message=str(payload["message"]),
            occurred_at=str(payload["occurred_at"]),
            started_at=str(payload["started_at"]),
            outcome=str(payload["outcome"]) if payload.get("outcome") else None,
        )


__all__ = ["MaintenanceEvent", "MaintenanceEventOutbox"]
