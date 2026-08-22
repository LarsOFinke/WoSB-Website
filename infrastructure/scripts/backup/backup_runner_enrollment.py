from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
from typing import Any

from backup_enrollment_contract import (
    REQUEST_KIND,
    SCHEMA_VERSION,
    canonical_json,
    parse_json_document,
    validate_request,
    validate_response,
)

from backup_runner_core import HOST_KEY_RE, HOST_RE, REMOTE_RE, USER_RE, now


class BackupEnrollmentMixin:
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
        lines = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip() and not line.startswith("#")
        ]
        if not lines:
            raise RuntimeError(
                "No SSH host key was returned. Check host, port and firewall."
            )
        fields = lines[0].split()
        if len(fields) < 3:
            raise RuntimeError("The SSH host-key response is malformed.")
        host_key = f"{fields[-2]} {fields[-1]}"
        if not HOST_KEY_RE.fullmatch(host_key):
            raise RuntimeError(
                "The discovered SSH host key uses an unsupported format."
            )
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

    def _key_identity(
        self, key_path: Path | None = None
    ) -> tuple[str | None, str | None]:
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
        if result.returncode != 0 or not public_key.startswith(
            ("ssh-ed25519 ", "ssh-rsa ", "ecdsa-")
        ):
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
        self.log(
            "Prepared the protected SSH upload key for manual backup-server configuration."
        )
        return {
            "upload_public_key": public_key,
            "upload_key_fingerprint": fingerprint,
        }

    def _public_key(self) -> str:
        if not self.key_file.is_file():
            temporary = self.run_dir / f"generated-backup-key.{os.getpid()}"
            result = subprocess.run(
                [
                    "ssh-keygen",
                    "-q",
                    "-t",
                    "ed25519",
                    "-N",
                    "",
                    "-C",
                    f"rbf-backup@{socket.gethostname()}",
                    "-f",
                    str(temporary),
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
        release_version = (self.infra_dir.parent / "VERSION").read_text(encoding="utf-8").strip()
        if not release_version or any(
            character not in "0123456789." for character in release_version
        ):
            raise RuntimeError("The installed application version is unavailable.")
        provisioner_path = (
            self.infra_dir.parent
            / "tools/backup-server/provision-rbf-backup-server.sh"
        )
        if (
            not provisioner_path.is_file()
            or provisioner_path.is_symlink()
            or provisioner_path.stat().st_size > 256 * 1024
        ):
            raise RuntimeError("The installed backup-server provisioner is unavailable.")
        provisioner = provisioner_path.read_bytes()
        ingest_path = self.infra_dir.parent / "tools/backup-server/rbf-backup-ingest.py"
        if (
            not ingest_path.is_file()
            or ingest_path.is_symlink()
            or ingest_path.stat().st_size > 256 * 1024
        ):
            raise RuntimeError("The installed backup-server ingest service is unavailable.")
        ingest_script = ingest_path.read_bytes()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": REQUEST_KIND,
            "enrollment_id": secrets.token_urlsafe(32),
            "created_at": now(),
            "product_hostname": socket.gethostname(),
            "release_version": release_version,
            "provisioner_base64": base64.b64encode(provisioner).decode("ascii"),
            "provisioner_sha256": hashlib.sha256(provisioner).hexdigest(),
            "ingest_script_base64": base64.b64encode(ingest_script).decode("ascii"),
            "ingest_script_sha256": hashlib.sha256(ingest_script).hexdigest(),
            "ssh_public_key": public_key,
            "requested_username": "rbf-backup",
            "requested_directory": "/incoming",
        }
        request = validate_request(payload)
        self._atomic_write(self.enrollment_request_file, canonical_json(request))
        self.log(
            "Created a public backup-server enrollment request and a protected SSH key."
        )
        return {
            "enrollment_request": request,
            "enrollment_id": request["enrollment_id"],
            "enrollment_public_key": public_key,
        }

    def _scan_host_key(self, host: str, port: int, expected_host_key: str) -> None:
        result = subprocess.run(
            [
                "ssh-keyscan",
                "-T",
                "10",
                "-p",
                str(port),
                "-t",
                "ed25519,rsa,ecdsa",
                host,
            ],
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
            raise RuntimeError(
                "The live SSH host key does not match the enrollment response."
            )

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
        receipt_directory: str | None = None,
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
            "receipt_directory": receipt_directory,
            "host_key_fingerprint": fingerprint,
            "managed_server": managed_server,
            "verification_mode": "sftp-roundtrip",
            "write_tested_at": write_tested_at,
        }
        self._atomic_write(
            self.config_file, json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        )
        self._atomic_write(self.known_hosts_file, known_hosts_line + "\n")
        os.chmod(self.key_file, 0o600)
        return config

    def apply_enrollment(self) -> dict[str, Any]:
        if not self.enrollment_request_file.is_file() or not self.key_file.is_file():
            raise RuntimeError(
                "Create an enrollment request before importing a response."
            )
        request = validate_request(self.read_json(self.enrollment_request_file))
        raw_response = str(self.request.get("response_json") or "")
        response = validate_response(
            parse_json_document(raw_response, "Enrollment response"),
            expected_enrollment_id=str(request["enrollment_id"]),
        )
        if response["managed_server"] is not True:
            raise RuntimeError(
                "The automatic enrollment path accepts only Recovery-Tool managed backup servers."
            )
        self._scan_host_key(
            str(response["host"]), int(response["port"]), str(response["host_key"])
        )
        token = self.known_hosts_token(str(response["host"]), int(response["port"]))
        fingerprint = self.fingerprint_for_line(f"{token} {response['host_key']}")
        if fingerprint != response["host_key_fingerprint"]:
            raise RuntimeError(
                "The enrollment response contains a wrong SSH host-key fingerprint."
            )

        protected_paths = [
            self.config_file,
            self.known_hosts_file,
            self.infra_dir / ".env",
        ]
        previous = {
            path: path.read_bytes() if path.is_file() else None
            for path in protected_paths
        }
        try:
            config = self._store_connection(
                host=str(response["host"]),
                port=int(response["port"]),
                username=str(response["username"]),
                remote_directory=str(response["remote_directory"]),
                receipt_directory=str(response["receipt_directory"]),
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
        self.log(
            "Applied the backup-server enrollment, enabled encrypted recovery backups and passed SFTP testing."
        )
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
        remote_directory = self.require_text(
            "remote_directory", REMOTE_RE, "remote directory"
        )
        if any(part in {"", ".", ".."} for part in remote_directory.split("/")[1:]):
            raise RuntimeError(
                "The remote directory contains unsupported path segments."
            )
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
        temporary_known_hosts = (
            self.run_dir / f"known-hosts.{os.getpid()}.{secrets.token_hex(4)}"
        )
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
        previous = {
            path: path.read_bytes() if path.is_file() else None
            for path in protected_paths
        }
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
