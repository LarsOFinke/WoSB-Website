from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


class BackupControlRepository:
    """Atomic filesystem gateway for the host-runner control contract."""

    def __init__(self, request_directory: Path, status_directory: Path) -> None:
        self.request_directory = request_directory
        self.status_directory = status_directory
        self.request_path = request_directory / "backup.request"
        self.status_path = status_directory / "backup-status.json"

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def read_status(self) -> dict[str, Any]:
        return self._read_json(self.status_path)

    def read_request(self) -> dict[str, Any]:
        return self._read_json(self.request_path)

    def request_exists(self) -> bool:
        return self.request_path.exists()

    def publish_request(self, payload: dict[str, Any]) -> None:
        self.request_directory.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.request_path.name}.",
            suffix=".tmp",
            dir=self.request_directory,
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            temporary.chmod(0o600)
            os.link(temporary, self.request_path)
            self.request_path.chmod(0o600)
            directory_descriptor = os.open(self.request_directory, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        finally:
            temporary.unlink(missing_ok=True)
