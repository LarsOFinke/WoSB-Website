#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from typing import Any


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
        if not self.config_file.is_file():
            return {"configured": False, "private_key_configured": self.key_file.is_file()}
        config = self.read_json(self.config_file)
        return {
            "configured": True,
            "host": config.get("host"),
            "port": config.get("port"),
            "username": config.get("username"),
            "remote_directory": config.get("remote_directory"),
            "host_key_fingerprint": config.get("host_key_fingerprint"),
            "private_key_configured": self.key_file.is_file(),
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
        token = self.known_hosts_token(host, port)
        known_hosts_line = f"{token} {host_key}"
        fingerprint = self.fingerprint_for_line(known_hosts_line)

        temporary_key: Path | None = None
        private_key = self.request.get("private_key")
        if isinstance(private_key, str) and private_key.strip():
            temporary_key = self.validate_private_key(private_key)
        elif not self.key_file.is_file():
            raise RuntimeError("A private key is required for the first backup connection setup.")

        temporary_config = self.run_dir / f"backup-config.{os.getpid()}.json"
        temporary_known_hosts = self.run_dir / f"known-hosts.{os.getpid()}"
        config = {
            "host": host,
            "port": port,
            "username": username,
            "remote_directory": remote_directory,
            "host_key_fingerprint": fingerprint,
        }
        temporary_config.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary_known_hosts.write_text(known_hosts_line + "\n", encoding="utf-8")
        os.chmod(temporary_config, 0o600)
        os.chmod(temporary_known_hosts, 0o600)
        os.replace(temporary_config, self.config_file)
        os.replace(temporary_known_hosts, self.known_hosts_file)
        if temporary_key is not None:
            os.replace(temporary_key, self.key_file)
        os.chmod(self.config_file, 0o600)
        os.chmod(self.known_hosts_file, 0o600)
        os.chmod(self.key_file, 0o600)
        self.log(f"Stored remote backup configuration for {username}@{host}:{port}{remote_directory}.")

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

    def ssh_base(self, config: dict[str, Any]) -> list[str]:
        return [
            "-P", str(config["port"]),
            "-i", str(self.key_file),
            "-o", "BatchMode=yes",
            "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={self.known_hosts_file}",
            "-o", "ConnectTimeout=15",
            f"{config['username']}@{config['host']}",
        ]

    def test_connection(self, config: dict[str, Any] | None = None) -> None:
        config = config or self.load_connection()
        batch = f"cd {config['remote_directory']}\npwd\nquit\n"
        self.log(f"Testing SFTP access to {config['host']}:{config['port']}{config['remote_directory']}.")
        result = subprocess.run(
            ["sftp", "-q", "-b", "-", *self.ssh_base(config)],
            input=batch,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["unknown SFTP error"]
            raise RuntimeError(f"SFTP connection test failed: {detail[0]}")

    def transfer(self, config: dict[str, Any], backup_file: Path, artifact_type: str) -> dict[str, Any]:
        checksum_file = Path(str(backup_file) + ".sha256")
        if not backup_file.is_file() or not checksum_file.is_file():
            raise RuntimeError("The local backup or checksum file is missing.")
        filename = backup_file.name
        checksum_name = checksum_file.name
        batch = "\n".join([
            f"cd {config['remote_directory']}",
            f"put {backup_file} {filename}.part",
            f"rename {filename}.part {filename}",
            f"put {checksum_file} {checksum_name}.part",
            f"rename {checksum_name}.part {checksum_name}",
            "quit",
            "",
        ])
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

        remote_command = (
            f"cd {shlex.quote(str(config['remote_directory']))} && "
            f"sha256sum -c {shlex.quote(checksum_name)}"
        )
        ssh_args = self.ssh_base(config)
        ssh_args[0] = "-p"
        verify = subprocess.run(
            ["ssh", *ssh_args, remote_command],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if verify.returncode != 0:
            raise RuntimeError("The remote checksum verification failed after upload.")

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

    def create_backup_artifact(
        self,
        *,
        config: dict[str, Any],
        script_name: str,
        artifact_type: str,
        description: str,
        timeout: int,
    ) -> dict[str, Any]:
        result_file = self.run_dir / f"backup-result-{artifact_type}.{os.getpid()}"
        result_file.unlink(missing_ok=True)
        env = os.environ.copy()
        env["BACKUP_RESULT_FILE"] = str(result_file)
        self.log(f"Creating a fresh {description} backup.")
        try:
            result = subprocess.run(
                ["/usr/bin/env", "bash", str(self.infra_dir / f"scripts/backup/{script_name}")],
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
            return self.transfer(config, backup_file, artifact_type)
        finally:
            result_file.unlink(missing_ok=True)

    def create_and_transfer_backup(self) -> dict[str, Any]:
        config = self.load_connection()
        self.test_connection(config)
        artifacts = [
            self.create_backup_artifact(
                config=config,
                script_name="backup-postgres.sh",
                artifact_type="postgresql",
                description="PostgreSQL database",
                timeout=1800,
            ),
            self.create_backup_artifact(
                config=config,
                script_name="backup-data.sh",
                artifact_type="files",
                description="uploaded files and operational data",
                timeout=1800,
            ),
        ]
        return {"artifacts": artifacts}

    def delete_configuration(self) -> None:
        if self.secret_dir.exists():
            shutil.rmtree(self.secret_dir)
        self.secret_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.secret_dir, 0o700)
        self.log("Removed the remote backup connection and its private key.")

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
            if operation == "discover":
                updates = self.discover()
                message = "SSH host key discovered. Verify its fingerprint before saving the connection."
            elif operation == "configure":
                self.configure()
                message = "Remote backup connection saved securely on the host."
            elif operation == "test":
                self.test_connection()
                message = "Remote backup connection test succeeded."
            elif operation == "backup":
                updates = self.create_and_transfer_backup()
                message = "Database and uploaded-file backups were created, transferred and verified successfully."
            elif operation == "delete_configuration":
                self.delete_configuration()
                message = "Remote backup connection removed."
            else:
                raise RuntimeError("Unsupported backup operation.")
            self.write_status("succeeded", message, started_at=started_at, finished_at=now(), **updates)
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            self.write_status("failed", str(exc), started_at=started_at, finished_at=now())
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
