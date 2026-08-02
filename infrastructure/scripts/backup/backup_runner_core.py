#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
for import_root in (SCRIPT_DIR, REPOSITORY_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))


HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
REMOTE_RE = re.compile(r"^/[A-Za-z0-9._/-]+$")
HOST_KEY_RE = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$"
)
ACTIVE_STATE = "running"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunnerCore:
    def __init__(self, infra_dir: Path, request_file: Path) -> None:
        self.infra_dir = infra_dir
        self.request_file = request_file
        self.control_root = infra_dir / "data/control"
        self.status_dir = self.control_root / "status"
        self.run_dir = self.control_root / "run"
        self.secret_dir = self.control_root / "secrets/backup-remote"
        self.status_file = self.status_dir / "backup-status.json"
        self.log_file = self.status_dir / "backup.log"
        self.config_file = self.secret_dir / "config.json"
        self.key_file = self.secret_dir / "id_backup"
        self.known_hosts_file = self.secret_dir / "known_hosts"
        self.enrollment_request_file = self.secret_dir / "enrollment-request.json"
        self.stop_heartbeat = threading.Event()
        self.request: dict[str, Any] = {}

    def prepare(self) -> None:
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.secret_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.status_dir, 0o755)
        os.chmod(self.run_dir, 0o700)
        os.chmod(self.secret_dir.parent, 0o700)
        os.chmod(self.secret_dir, 0o700)
        self.log_file.touch(exist_ok=True)
        os.chmod(self.log_file, 0o644)

    def log(self, message: str) -> None:
        line = (
            f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}"
        )
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        print(line, flush=True)

    def read_json(self, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Invalid JSON file: {path.name}") from exc
        if not isinstance(payload, dict):
            raise RuntimeError(f"JSON file must contain an object: {path.name}")
        return payload

    def connection_summary(self) -> dict[str, Any]:
        public_key, key_fingerprint = self._key_identity()
        if not self.config_file.is_file():
            return {
                "configured": False,
                "private_key_configured": self.key_file.is_file(),
                "upload_public_key": public_key,
                "upload_key_fingerprint": key_fingerprint,
                "write_tested_at": None,
            }
        config = self.read_json(self.config_file)
        return {
            "configured": True,
            "host": config.get("host"),
            "port": config.get("port"),
            "username": config.get("username"),
            "remote_directory": config.get("remote_directory"),
            "host_key_fingerprint": config.get("host_key_fingerprint"),
            "private_key_configured": self.key_file.is_file(),
            "upload_public_key": public_key,
            "upload_key_fingerprint": key_fingerprint,
            "write_tested_at": config.get("write_tested_at"),
            "managed_server": config.get("managed_server") is True,
        }

    def old_status(self) -> dict[str, Any]:
        if not self.status_file.is_file():
            return {}
        try:
            payload = json.loads(self.status_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def write_status(self, state: str, message: str, **updates: Any) -> None:
        old = self.old_status()
        payload = {
            **old,
            "state": state,
            "operation": self.request.get("operation")
            or old.get("operation")
            or "idle",
            "message": message,
            "requested_by": self.request.get("requested_by") or old.get("requested_by"),
            "requested_at": self.request.get("requested_at") or old.get("requested_at"),
            "connection": self.connection_summary(),
            **updates,
        }
        if state == ACTIVE_STATE:
            payload["heartbeat_at"] = now()
        elif state in {"succeeded", "failed"}:
            payload["heartbeat_at"] = None
        temporary = self.status_file.with_name(
            f".{self.status_file.name}.{os.getpid()}.tmp"
        )
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.chmod(temporary, 0o644)
        os.replace(temporary, self.status_file)

    def heartbeat(self) -> None:
        while not self.stop_heartbeat.wait(30):
            try:
                status = self.old_status()
                if status.get("state") != ACTIVE_STATE:
                    return
                self.write_status(
                    ACTIVE_STATE,
                    str(status.get("message") or "Backup operation running."),
                )
            except Exception:
                pass

    def require_text(self, key: str, pattern: re.Pattern[str], label: str) -> str:
        value = str(self.request.get(key) or "").strip()
        if not pattern.fullmatch(value):
            raise RuntimeError(f"Invalid {label}.")
        return value

    def require_port(self) -> int:
        try:
            port = int(self.request.get("port") or 22)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Invalid SSH port.") from exc
        if not 1 <= port <= 65535:
            raise RuntimeError("Invalid SSH port.")
        return port

    @staticmethod
    def known_hosts_token(host: str, port: int) -> str:
        return host if port == 22 else f"[{host}]:{port}"

    def fingerprint_for_line(self, line: str) -> str:
        temporary = self.run_dir / f"known-host.{os.getpid()}"
        temporary.write_text(line.rstrip() + "\n", encoding="utf-8")
        try:
            result = subprocess.run(
                ["ssh-keygen", "-lf", str(temporary)],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            temporary.unlink(missing_ok=True)
        parts = result.stdout.strip().split()
        if len(parts) < 2:
            raise RuntimeError("Could not calculate the SSH host-key fingerprint.")
        return parts[1]
