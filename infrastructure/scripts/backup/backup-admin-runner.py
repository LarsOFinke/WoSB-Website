#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
for import_root in (SCRIPT_DIR, REPOSITORY_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from contracts.backup_enrollment import (  # noqa: E402
    REQUEST_KIND,
    SCHEMA_VERSION,
    canonical_json,
    parse_json_document,
    validate_request,
    validate_response,
)
from local_backup_catalog import (  # noqa: E402
    consume_database_restore_approval,
    resolve_local_postgres_backup,
    scan_local_postgres_backups,
)


HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
REMOTE_RE = re.compile(r"^/[A-Za-z0-9._/-]+$")
HOST_KEY_RE = re.compile(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$")
ACTIVE_STATE = "running"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Runner:
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
        line = f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}"
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
            "operation": self.request.get("operation") or old.get("operation") or "idle",
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
        temporary = self.status_file.with_name(f".{self.status_file.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o644)
        os.replace(temporary, self.status_file)

    def heartbeat(self) -> None:
        while not self.stop_heartbeat.wait(30):
            try:
                status = self.old_status()
                if status.get("state") != ACTIVE_STATE:
                    return
                self.write_status(ACTIVE_STATE, str(status.get("message") or "Backup operation running."))
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

    def discover(self) -> dict[str, Any]:
        host = self.require_text("host", HOST_RE, "backup host")
        port = self.require_port()
        self.log(f"Discovering SSH host key for {host}:{port}.")
        result = subprocess.run(
            ["ssh-keyscan", "-T", "10", "-p", str(port), "-t", "ed25519,rsa", host],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("#")]
        if not lines:
            raise RuntimeError("No SSH host key was returned. Check host, port and firewall.")
        fields = lines[0].split()
        if len(fields) < 3:
            raise RuntimeError("The SSH host-key response is malformed.")
        host_key = f"{fields[-2]} {fields[-1]}"
        if not HOST_KEY_RE.fullmatch(host_key):
            raise RuntimeError("The discovered SSH host key uses an unsupported format.")
        token = self.known_hosts_token(host, port)
        fingerprint = self.fingerprint_for_line(f"{token} {host_key}")
        return {
            "discovered_host": host,
            "discovered_port": port,
            "discovered_host_key": host_key,
            "discovered_fingerprint": fingerprint,
        }

    def _atomic_write(self, path: Path, content: str, mode: int = 0o600) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(content, encoding="utf-8")
        os.chmod(temporary, mode)
        os.replace(temporary, path)

    def _key_identity(self, key_path: Path | None = None) -> tuple[str | None, str | None]:
        path = key_path or self.key_file
        if not path.is_file():
            return None, None
        result = subprocess.run(
            ["ssh-keygen", "-y", "-f", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        public_key = result.stdout.strip()
        if result.returncode != 0 or not public_key.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-")):
            raise RuntimeError("Could not derive the public SSH backup key.")
        public_file = self.run_dir / f"public-key.{os.getpid()}.{secrets.token_hex(4)}"
        public_file.write_text(public_key + "\n", encoding="utf-8")
        try:
            fingerprint_result = subprocess.run(
                ["ssh-keygen", "-lf", str(public_file)],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            public_file.unlink(missing_ok=True)
        parts = fingerprint_result.stdout.strip().split()
        if fingerprint_result.returncode != 0 or len(parts) < 2:
            raise RuntimeError("Could not calculate the SSH upload-key fingerprint.")
        return f"{public_key} rbf-backup@{socket.gethostname()}", parts[1]

    def prepare_key(self) -> dict[str, Any]:
        self._public_key()
        public_key, fingerprint = self._key_identity()
        self.log("Prepared the protected SSH upload key for manual backup-server configuration.")
        return {
            "upload_public_key": public_key,
            "upload_key_fingerprint": fingerprint,
        }

    def _public_key(self) -> str:
        if not self.key_file.is_file():
            temporary = self.run_dir / f"generated-backup-key.{os.getpid()}"
            result = subprocess.run(
                [
                    "ssh-keygen", "-q", "-t", "ed25519", "-N", "",
                    "-C", f"rbf-backup@{socket.gethostname()}", "-f", str(temporary),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0 or not temporary.is_file():
                raise RuntimeError("Could not generate the dedicated SSH backup key.")
            os.replace(temporary, self.key_file)
            Path(f"{temporary}.pub").unlink(missing_ok=True)
            os.chmod(self.key_file, 0o600)
        public_key, _ = self._key_identity()
        if not public_key:
            raise RuntimeError("Could not derive the public SSH backup key.")
        return public_key

    def prepare_enrollment(self) -> dict[str, Any]:
        public_key = self._public_key()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": REQUEST_KIND,
            "enrollment_id": secrets.token_urlsafe(32),
            "created_at": now(),
            "product_hostname": socket.gethostname(),
            "ssh_public_key": public_key,
            "requested_username": "rbf-backup",
            "requested_directory": "/data",
        }
        request = validate_request(payload)
        self._atomic_write(self.enrollment_request_file, canonical_json(request))
        self.log("Created a public backup-server enrollment request and a protected SSH key.")
        return {
            "enrollment_request": request,
            "enrollment_id": request["enrollment_id"],
            "enrollment_public_key": public_key,
        }

    def _scan_host_key(self, host: str, port: int, expected_host_key: str) -> None:
        result = subprocess.run(
            ["ssh-keyscan", "-T", "10", "-p", str(port), "-t", "ed25519,rsa,ecdsa", host],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        discovered = set()
        for line in result.stdout.splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) >= 3:
                discovered.add(f"{fields[-2]} {fields[-1]}")
        if expected_host_key not in discovered:
            raise RuntimeError("The live SSH host key does not match the enrollment response.")

    @staticmethod
    def _set_env_values(path: Path, updates: dict[str, str]) -> None:
        if not path.is_file():
            raise RuntimeError("The infrastructure .env file is missing.")
        lines = path.read_text(encoding="utf-8").splitlines()
        remaining = dict(updates)
        rendered: list[str] = []
        for line in lines:
            if "=" not in line or line.lstrip().startswith("#"):
                rendered.append(line)
                continue
            key = line.split("=", 1)[0].strip()
            if key in remaining:
                value = remaining.pop(key)
                rendered.append(f"{key}={value}")
            else:
                rendered.append(line)
        for key, value in remaining.items():
            rendered.append(f"{key}={value}")
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text("\n".join(rendered) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)

    def _store_connection(
        self,
        *,
        host: str,
        port: int,
        username: str,
        remote_directory: str,
        host_key: str,
        managed_server: bool = False,
        write_tested_at: str | None = None,
    ) -> dict[str, Any]:
        token = self.known_hosts_token(host, port)
        known_hosts_line = f"{token} {host_key}"
        fingerprint = self.fingerprint_for_line(known_hosts_line)
        config = {
            "host": host,
            "port": port,
            "username": username,
            "remote_directory": remote_directory,
            "host_key_fingerprint": fingerprint,
            "managed_server": managed_server,
            "verification_mode": "sftp-roundtrip",
            "write_tested_at": write_tested_at,
        }
        self._atomic_write(self.config_file, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        self._atomic_write(self.known_hosts_file, known_hosts_line + "\n")
        os.chmod(self.key_file, 0o600)
        return config

    def apply_enrollment(self) -> dict[str, Any]:
        if not self.enrollment_request_file.is_file() or not self.key_file.is_file():
            raise RuntimeError("Create an enrollment request before importing a response.")
        request = validate_request(self.read_json(self.enrollment_request_file))
        raw_response = str(self.request.get("response_json") or "")
        response = validate_response(
            parse_json_document(raw_response, "Enrollment response"),
            expected_enrollment_id=str(request["enrollment_id"]),
        )
        if response["managed_server"] is not True:
            raise RuntimeError("The automatic enrollment path accepts only Recovery-Tool managed backup servers.")
        self._scan_host_key(str(response["host"]), int(response["port"]), str(response["host_key"]))
        token = self.known_hosts_token(str(response["host"]), int(response["port"]))
        fingerprint = self.fingerprint_for_line(f"{token} {response['host_key']}")
        if fingerprint != response["host_key_fingerprint"]:
            raise RuntimeError("The enrollment response contains a wrong SSH host-key fingerprint.")

        protected_paths = [self.config_file, self.known_hosts_file, self.infra_dir / ".env"]
        previous = {path: path.read_bytes() if path.is_file() else None for path in protected_paths}
        try:
            config = self._store_connection(
                host=str(response["host"]),
                port=int(response["port"]),
                username=str(response["username"]),
                remote_directory=str(response["remote_directory"]),
                host_key=str(response["host_key"]),
                managed_server=bool(response["managed_server"]),
            )
            self._set_env_values(
                self.infra_dir / ".env",
                {
                    "BACKUP_RECOVERY_ENABLED": "true",
                    "BACKUP_AGE_RECIPIENT": str(response["age_recipient"]),
                },
            )
            self.test_connection(config)
        except Exception:
            for path, content in previous.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    self._atomic_write(path, content.decode("utf-8"))
            raise
        self.enrollment_request_file.unlink(missing_ok=True)
        self.log("Applied the backup-server enrollment, enabled encrypted recovery backups and passed SFTP testing.")
        return {
            "enrollment_applied": True,
            "enrollment_id": response["enrollment_id"],
            "enrollment_request": None,
            "enrollment_public_key": None,
            "age_recipient_configured": True,
        }

    def validate_private_key(self, content: str) -> Path:
        temporary = self.run_dir / f"private-key.{os.getpid()}"
        temporary.write_text(content.rstrip() + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        result = subprocess.run(
            ["ssh-keygen", "-y", "-f", str(temporary)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("The supplied private key could not be read by OpenSSH.")
        return temporary

    def configure(self) -> None:
        host = self.require_text("host", HOST_RE, "backup host")
        port = self.require_port()
        username = self.require_text("username", USER_RE, "SSH username")
        remote_directory = self.require_text("remote_directory", REMOTE_RE, "remote directory")
        if any(part in {"", ".", ".."} for part in remote_directory.split("/")[1:]):
            raise RuntimeError("The remote directory contains unsupported path segments.")
        host_key = " ".join(str(self.request.get("host_key") or "").split())
        if not HOST_KEY_RE.fullmatch(host_key):
            raise RuntimeError("Invalid SSH host key.")

        temporary_key: Path | None = None
        private_key = self.request.get("private_key")
        if isinstance(private_key, str) and private_key.strip():
            temporary_key = self.validate_private_key(private_key)
            candidate_key = temporary_key
        elif self.key_file.is_file():
            candidate_key = self.key_file
        else:
            raise RuntimeError(
                "A private key is required, or prepare the protected upload key in the web interface first."
            )

        token = self.known_hosts_token(host, port)
        temporary_known_hosts = self.run_dir / f"known-hosts.{os.getpid()}.{secrets.token_hex(4)}"
        temporary_known_hosts.write_text(f"{token} {host_key}\n", encoding="utf-8")
        os.chmod(temporary_known_hosts, 0o600)
        config = {
            "host": host,
            "port": port,
            "username": username,
            "remote_directory": remote_directory,
            "managed_server": False,
        }
        protected_paths = [self.key_file, self.config_file, self.known_hosts_file]
        previous = {path: path.read_bytes() if path.is_file() else None for path in protected_paths}
        try:
            tested_at = self.test_connection(
                config,
                key_path=candidate_key,
                known_hosts_file=temporary_known_hosts,
                persist=False,
            )
            try:
                if temporary_key is not None:
                    os.replace(temporary_key, self.key_file)
                    temporary_key = None
                self._store_connection(
                    host=host,
                    port=port,
                    username=username,
                    remote_directory=remote_directory,
                    host_key=host_key,
                    managed_server=False,
                    write_tested_at=tested_at,
                )
            except Exception:
                for path, content in previous.items():
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        self._atomic_write(path, content.decode("utf-8"))
                raise
        finally:
            temporary_known_hosts.unlink(missing_ok=True)
            if temporary_key is not None:
                temporary_key.unlink(missing_ok=True)
        self.log(
            f"Stored and write-tested remote backup configuration for "
            f"{username}@{host}:{port}{remote_directory}."
        )

    def load_connection(self) -> dict[str, Any]:
        if not self.config_file.is_file() or not self.key_file.is_file() or not self.known_hosts_file.is_file():
            raise RuntimeError("Configure the remote backup connection first.")
        config = self.read_json(self.config_file)
        host = str(config.get("host") or "")
        username = str(config.get("username") or "")
        remote_directory = str(config.get("remote_directory") or "")
        port = int(config.get("port") or 22)
        if not HOST_RE.fullmatch(host) or not USER_RE.fullmatch(username) or not REMOTE_RE.fullmatch(remote_directory):
            raise RuntimeError("The stored backup configuration is invalid.")
        return config

    def ssh_base(
        self,
        config: dict[str, Any],
        *,
        key_path: Path | None = None,
        known_hosts_file: Path | None = None,
    ) -> list[str]:
        return [
            "-P", str(config["port"]),
            "-i", str(key_path or self.key_file),
            "-o", "BatchMode=yes",
            "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={known_hosts_file or self.known_hosts_file}",
            "-o", "ConnectTimeout=15",
            f"{config['username']}@{config['host']}",
        ]

    @staticmethod
    def _sftp_error_detail(result: subprocess.CompletedProcess[str]) -> str:
        lines = [
            line.strip()
            for line in f"{result.stderr or ''}\n{result.stdout or ''}".splitlines()
            if line.strip() and not line.lstrip().startswith("sftp>")
        ]
        preferred = [
            line for line in lines
            if any(marker in line.lower() for marker in (
                "permission denied", "no such file", "failure", "not found",
                "host key verification", "connection refused", "connection closed",
            ))
        ]
        return (preferred or lines or ["unknown SFTP error"])[-1]

    def _sftp_roundtrip(
        self,
        config: dict[str, Any],
        *,
        key_path: Path | None = None,
        known_hosts_file: Path | None = None,
    ) -> None:
        token = secrets.token_hex(12)
        source = self.run_dir / f"sftp-write-test.{token}"
        downloaded = self.run_dir / f"sftp-write-test.{token}.download"
        remote_part = f".rbf-write-test-{token}.part"
        remote_final = f".rbf-write-test-{token}"
        payload = secrets.token_bytes(64)
        source.write_bytes(payload)
        os.chmod(source, 0o600)
        batch = "\n".join([
            f"cd {config['remote_directory']}",
            f"put {source} {remote_part}",
            f"rename {remote_part} {remote_final}",
            f"get {remote_final} {downloaded}",
            f"rm {remote_final}",
            "quit",
            "",
        ])
        try:
            result = subprocess.run(
                [
                    "sftp", "-q", "-b", "-",
                    *self.ssh_base(
                        config,
                        key_path=key_path,
                        known_hosts_file=known_hosts_file,
                    ),
                ],
                input=batch,
                text=True,
                capture_output=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(f"SFTP write test failed: {self._sftp_error_detail(result)}")
            if not downloaded.is_file() or downloaded.read_bytes() != payload:
                raise RuntimeError("SFTP write test failed: the downloaded test payload did not match.")
        finally:
            source.unlink(missing_ok=True)
            downloaded.unlink(missing_ok=True)

    def test_connection(
        self,
        config: dict[str, Any] | None = None,
        *,
        key_path: Path | None = None,
        known_hosts_file: Path | None = None,
        persist: bool = True,
    ) -> str:
        config = config or self.load_connection()
        self.log(
            f"Testing SFTP write/read/delete access to "
            f"{config['host']}:{config['port']}{config['remote_directory']}."
        )
        self._sftp_roundtrip(
            config,
            key_path=key_path,
            known_hosts_file=known_hosts_file,
        )
        tested_at = now()
        if persist and self.config_file.is_file():
            stored = self.read_json(self.config_file)
            stored["verification_mode"] = "sftp-roundtrip"
            stored["write_tested_at"] = tested_at
            self._atomic_write(self.config_file, json.dumps(stored, ensure_ascii=False, indent=2) + "\n")
        return tested_at

    def transfer(self, config: dict[str, Any], backup_file: Path, artifact_type: str) -> dict[str, Any]:
        checksum_file = Path(str(backup_file) + ".sha256")
        if not backup_file.is_file() or not checksum_file.is_file():
            raise RuntimeError("The local backup or checksum file is missing.")
        filename = backup_file.name
        checksum_name = checksum_file.name
        metadata_file = Path(str(backup_file) + ".restore.json")
        metadata_checksum = Path(str(metadata_file) + ".sha256")
        commands = [f"cd {config['remote_directory']}"]
        if artifact_type == "backup_set":
            # Publish the checksum first and the manifest itself last. Consumers
            # can therefore use the manifest as the atomic remote commit marker.
            commands.extend([
                f"put {checksum_file} {checksum_name}.part",
                f"rename {checksum_name}.part {checksum_name}",
                f"put {backup_file} {filename}.part",
                f"rename {filename}.part {filename}",
            ])
        else:
            commands.extend([
                f"put {backup_file} {filename}.part",
                f"rename {filename}.part {filename}",
                f"put {checksum_file} {checksum_name}.part",
                f"rename {checksum_name}.part {checksum_name}",
            ])
        if metadata_file.is_file() and metadata_checksum.is_file():
            metadata_name = metadata_file.name
            metadata_checksum_name = metadata_checksum.name
            commands.extend([
                f"put {metadata_file} {metadata_name}.part",
                f"rename {metadata_name}.part {metadata_name}",
                f"put {metadata_checksum} {metadata_checksum_name}.part",
                f"rename {metadata_checksum_name}.part {metadata_checksum_name}",
            ])
        commands.extend(["quit", ""])
        batch = "\n".join(commands)
        self.log(f"Transferring {filename} and checksum to the configured backup server.")
        result = subprocess.run(
            ["sftp", "-q", "-b", "-", *self.ssh_base(config)],
            input=batch,
            text=True,
            capture_output=True,
            timeout=900,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["unknown SFTP error"]
            raise RuntimeError(f"Backup transfer failed: {detail[0]}")

        verification_sources = [backup_file, checksum_file]
        if metadata_file.is_file() and metadata_checksum.is_file():
            verification_sources.extend([metadata_file, metadata_checksum])
        # All upload accounts may be SFTP-only. Verify every remote object by
        # downloading it through the same pinned SFTP channel and comparing its
        # digest locally; never require a remote shell merely for checksum work.
        for source in verification_sources:
            with tempfile.NamedTemporaryFile(
                prefix="rbf-remote-verify-",
                dir=self.run_dir,
                delete=False,
            ) as handle:
                verification_copy = Path(handle.name)
            try:
                batch = f"cd {config['remote_directory']}\nget {source.name} {verification_copy}\nquit\n"
                download = subprocess.run(
                    ["sftp", "-q", "-b", "-", *self.ssh_base(config)],
                    input=batch,
                    text=True,
                    capture_output=True,
                    timeout=900,
                )
                if download.returncode != 0:
                    raise RuntimeError(
                        "The remote SFTP verification failed after upload: "
                        f"{self._sftp_error_detail(download)}"
                    )
                if hashlib.sha256(verification_copy.read_bytes()).hexdigest() != hashlib.sha256(source.read_bytes()).hexdigest():
                    raise RuntimeError("The remote SFTP verification failed after upload: digest mismatch.")
            finally:
                verification_copy.unlink(missing_ok=True)

        digest_builder = hashlib.sha256()
        with backup_file.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest_builder.update(chunk)
        digest = digest_builder.hexdigest()
        return {
            "artifact_type": artifact_type,
            "filename": filename,
            "size_bytes": backup_file.stat().st_size,
            "sha256": digest,
            "remote_path": f"{config['remote_directory'].rstrip('/')}/{filename}",
        }

    def create_local_backup_artifact(
        self,
        *,
        script_name: str,
        artifact_type: str,
        description: str,
        timeout: int,
        arguments: list[str] | None = None,
    ) -> Path:
        result_file = self.run_dir / f"backup-result-{artifact_type}.{os.getpid()}"
        result_file.unlink(missing_ok=True)
        env = os.environ.copy()
        env["BACKUP_RESULT_FILE"] = str(result_file)
        self.log(f"Creating a fresh {description} backup.")
        try:
            command = ["/usr/bin/env", "bash", str(self.infra_dir / f"scripts/backup/{script_name}")]
            if arguments:
                command.extend(arguments)
            result = subprocess.run(
                command,
                env=env,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
            for line in (result.stdout or "").splitlines():
                self.log(line)
            if result.returncode != 0 or not result_file.is_file():
                raise RuntimeError(f"{description.capitalize()} backup creation failed.")
            backup_path = result_file.read_text(encoding="utf-8").strip()
            backup_file = Path(backup_path)
            if not backup_file.is_absolute():
                raise RuntimeError(f"{description.capitalize()} backup returned an invalid path.")
            return backup_file
        finally:
            result_file.unlink(missing_ok=True)

    def recovery_enabled(self) -> bool:
        env_file = self.infra_dir / ".env"
        if not env_file.is_file():
            return False
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "BACKUP_RECOVERY_ENABLED":
                return value.strip().strip("\"'").lower() in {"1", "true", "yes", "on"}
        return False

    def create_and_transfer_backup(self) -> dict[str, Any]:
        config = self.load_connection()
        result_files = {
            name: self.run_dir / f"backup-result-{name}.{os.getpid()}"
            for name in ("postgres", "files", "recovery", "verification", "set")
        }
        for path in result_files.values():
            path.unlink(missing_ok=True)
        command = [
            "/usr/bin/env",
            "bash",
            str(self.infra_dir / "scripts/backup/run-consistent-backup.sh"),
            "--all-locks-held",
            "--reason", "admin-requested",
            "--postgres-result", str(result_files["postgres"]),
            "--files-result", str(result_files["files"]),
            "--recovery-result", str(result_files["recovery"]),
            "--verification-result", str(result_files["verification"]),
            "--backup-set-result", str(result_files["set"]),
        ]
        if self.recovery_enabled():
            command.append("--include-recovery")
        self.log("Creating one coordinated backup set and proving full recoverability before transfer.")
        try:
            result = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10800,
            )
            for line in (result.stdout or "").splitlines():
                self.log(line)
            if result.returncode != 0:
                raise RuntimeError("Coordinated backup or recovery verification failed.")
            required = ("postgres", "files", "verification", "set")
            if any(not result_files[name].is_file() for name in required):
                raise RuntimeError("The coordinated backup did not return every required artifact.")
            paths = {
                name: Path(result_files[name].read_text(encoding="utf-8").strip())
                for name in required
            }
            if self.recovery_enabled():
                if not result_files["recovery"].is_file():
                    raise RuntimeError("Encrypted recovery bundle was enabled but not returned.")
                paths["recovery"] = Path(result_files["recovery"].read_text(encoding="utf-8").strip())
            artifacts = [
                self.transfer(config, paths["postgres"], "postgresql"),
                self.transfer(config, paths["files"], "files"),
            ]
            if "recovery" in paths:
                artifacts.append(self.transfer(config, paths["recovery"], "recovery"))
            # The verification report is uploaded before the manifest. The manifest is
            # the remote commit marker and is deliberately transferred last.
            self.transfer(config, paths["verification"], "verification")
            self.transfer(config, paths["set"], "backup_set")
            return {"artifacts": artifacts}
        finally:
            for path in result_files.values():
                path.unlink(missing_ok=True)

    def local_catalog_updates(self) -> dict[str, Any]:
        records, skipped = scan_local_postgres_backups(self.infra_dir)
        return {
            "local_database_backups": [record.public_dict() for record in records],
            "local_catalog_updated_at": now(),
            "local_catalog_skipped_count": skipped,
        }

    def scan_local_backups(self) -> dict[str, Any]:
        self.log("Scanning the protected local PostgreSQL backup directory.")
        updates = self.local_catalog_updates()
        self.log(
            "Verified "
            f"{len(updates['local_database_backups'])} local PostgreSQL backup(s); "
            f"skipped {updates['local_catalog_skipped_count']} invalid entry or entries."
        )
        return updates

    def restore_postgresql(self) -> dict[str, Any]:
        backup_id = str(self.request.get("backup_id") or "")
        approval_token_sha256 = str(self.request.get("approval_token_sha256") or "")
        # Consume host approval before any catalog hashing or gzip work. Every request,
        # including a malformed selection, therefore needs a fresh physical-host action.
        consume_database_restore_approval(self.infra_dir, approval_token_sha256)
        self.request.pop("approval_token_sha256", None)
        record = resolve_local_postgres_backup(self.infra_dir, backup_id)
        if not record.restore_metadata_verified:
            raise RuntimeError("The admin restore path rejects backups without verified restore metadata.")
        if not record.production_consistent:
            raise RuntimeError("The admin restore path rejects uncoordinated live snapshots.")
        if not record.backup_set_verified:
            raise RuntimeError("The backup is not bound to a validated recovery-tested backup set.")
        if record.encryption_keys_compatible is False:
            raise RuntimeError(
                "The selected database backup was created with a different secret-encryption "
                "key ring. Restore the matching full recovery bundle or import the old "
                "WEBHOOK_ENCRYPTION_KEYS before retrying."
            )
        if record.filename.endswith(".gz"):
            preflight = subprocess.run(
                ["gzip", "-t", str(record.path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if preflight.returncode != 0:
                raise RuntimeError("The selected compressed database backup failed validation.")
        self.log(f"Starting approved PostgreSQL restore from {record.filename}.")
        env = os.environ.copy()
        env["RBF_RESTORE_LOCK_HELD"] = "true"
        result = subprocess.run(
            [
                "/usr/bin/env",
                "bash",
                str(self.infra_dir / "scripts/backup/restore-postgres.sh"),
                str(record.path),
            ],
            env=env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=7200,
        )
        for line in (result.stdout or "").splitlines():
            self.log(line)
        if result.returncode != 0:
            raise RuntimeError("The controlled PostgreSQL restore failed; review host logs.")
        return self.local_catalog_updates()

    @staticmethod
    def public_failure_message(operation: str) -> str:
        messages = {
            "prepare_key": "The protected SSH upload key could not be prepared.",
            "discover": "SSH host-key discovery failed. Review the protected host log.",
            "configure": "The remote backup connection could not be saved. Review the protected host log.",
            "prepare_enrollment": "The enrollment request could not be created.",
            "apply_enrollment": "The enrollment response could not be applied or verified.",
            "test": "The remote backup connection test failed. Review the protected host log.",
            "backup": "The application backup failed. Review the protected host log.",
            "delete_configuration": "The remote backup connection could not be removed.",
            "scan_local_backups": "The protected local backup catalog could not be refreshed.",
            "restore_postgresql": (
                "The database restore was rejected or failed. Create a new host approval token "
                "if needed and review the protected host log before retrying."
            ),
        }
        return messages.get(operation, "The protected host operation failed.")

    def delete_configuration(self) -> dict[str, Any]:
        if self.secret_dir.exists():
            shutil.rmtree(self.secret_dir)
        self.secret_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.secret_dir, 0o700)
        self.log("Removed the remote backup connection and its private key.")
        return {
            "enrollment_request": None,
            "enrollment_id": None,
            "enrollment_public_key": None,
            "enrollment_applied": False,
        }

    def run(self) -> None:
        self.prepare()
        self.request = self.read_json(self.request_file)
        self.request_file.unlink(missing_ok=True)
        operation = str(self.request.get("operation") or "")
        started_at = now()
        self.write_status(ACTIVE_STATE, "Backup operation is running.", started_at=started_at, finished_at=None)
        thread = threading.Thread(target=self.heartbeat, daemon=True)
        thread.start()
        try:
            updates: dict[str, Any] = {}
            if operation == "prepare_key":
                updates = self.prepare_key()
                message = "Protected SSH upload key prepared. Install the displayed public key on the backup server."
            elif operation == "prepare_enrollment":
                updates = self.prepare_enrollment()
                message = "Enrollment request created. Provision the backup server with the Recovery Tool."
            elif operation == "apply_enrollment":
                updates = self.apply_enrollment()
                message = "Backup server enrolled, encrypted recovery enabled and SFTP connection verified."
            elif operation == "discover":
                updates = self.discover()
                message = "SSH host key discovered. Verify its fingerprint before saving the connection."
            elif operation == "configure":
                self.configure()
                message = "Remote backup connection saved after a successful SFTP write/read/delete test."
            elif operation == "test":
                self.test_connection()
                message = "Remote SFTP write/read/delete test succeeded."
            elif operation == "backup":
                updates = self.create_and_transfer_backup()
                message = "Database, uploaded-file and any enabled encrypted recovery backups were created, transferred and verified successfully."
            elif operation == "delete_configuration":
                updates = self.delete_configuration()
                message = "Remote backup connection removed."
            elif operation == "scan_local_backups":
                updates = self.scan_local_backups()
                message = "The protected local PostgreSQL backup catalog was refreshed."
            elif operation == "restore_postgresql":
                updates = self.restore_postgresql()
                message = "The selected PostgreSQL backup was restored and the application passed its checks."
            else:
                raise RuntimeError("Unsupported backup operation.")
            self.write_status("succeeded", message, started_at=started_at, finished_at=now(), **updates)
        except Exception as exc:
            self.request.pop("approval_token_sha256", None)
            self.log(f"ERROR: {exc}")
            self.write_status(
                "failed",
                self.public_failure_message(operation),
                started_at=started_at,
                finished_at=now(),
            )
            raise
        finally:
            self.stop_heartbeat.set()
            thread.join(timeout=2)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: backup-admin-runner.py INFRA_DIR CLAIMED_REQUEST", file=sys.stderr)
        return 2
    runner = Runner(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
