from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path


MAINTENANCE_FILE = "maintenance-mode.json"
MAINTENANCE_REASONS = {"manual", "restart", "restore", "update"}


@dataclass(frozen=True)
class MaintenanceMode:
    reason: str
    message: str
    started_at: str
    retry_after_seconds: int


class ServiceAvailability:
    """Own the small filesystem contract shared by host runners and NGINX."""

    def __init__(self, status_dir: Path) -> None:
        self.status_dir = status_dir
        self.path = status_dir / MAINTENANCE_FILE

    def enable(
        self,
        *,
        reason: str,
        message: str,
        retry_after_seconds: int = 120,
    ) -> MaintenanceMode:
        normalized_reason = reason.strip().lower()
        if normalized_reason not in MAINTENANCE_REASONS:
            raise ValueError(f"Unsupported maintenance reason: {reason}")
        normalized_message = " ".join(message.split()).strip()
        if not normalized_message or len(normalized_message) > 240:
            raise ValueError("Maintenance message must contain 1 to 240 characters.")
        state = MaintenanceMode(
            reason=normalized_reason,
            message=normalized_message,
            started_at=datetime.now(timezone.utc).isoformat(),
            retry_after_seconds=max(30, min(int(retry_after_seconds), 3600)),
        )
        self.status_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.status_dir / f".{MAINTENANCE_FILE}.{os.getpid()}.tmp"
        temporary.write_text(
            json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(0o644)
        os.replace(temporary, self.path)
        self.path.chmod(0o644)
        return state

    def disable(self) -> bool:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return False
        return True

    def read(self) -> MaintenanceMode | None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return MaintenanceMode(
                reason=str(payload["reason"]),
                message=str(payload["message"]),
                started_at=str(payload["started_at"]),
                retry_after_seconds=int(payload["retry_after_seconds"]),
            )
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            return None


__all__ = ["MAINTENANCE_FILE", "MaintenanceMode", "ServiceAvailability"]
