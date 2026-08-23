from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tarfile
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
    def _install_pull_endpoint(self, response: dict[str, Any]) -> None:
        environment = str(response["deployment_environment"])
        username = str(response["username"])
        public_key = str(response["controller_public_key"])
        if username != f"rbf-backup-controller-{environment}":
            raise RuntimeError("The backup-controller identity is invalid.")
        if response.get("transport") != "recovery-controller-pull-v1":
            raise RuntimeError("The backup-controller transport is invalid.")

        state_dir = Path("/etc/rbf-backup-pull")
        state_file = state_dir / f"{username}.json"
        auth_dir = Path("/etc/ssh/authorized_keys")
        auth_file = auth_dir / username
        dropin_dir = Path("/etc/ssh/sshd_config.d")
        dropin_file = dropin_dir / f"91-{username}-managed.conf"
        chroot = Path(f"/var/lib/rbf-backup-pull/{environment}")
        account = subprocess.run(
            ["getent", "passwd", username], check=False, capture_output=True, text=True
        )
        if account.returncode == 0 and not state_file.is_file():
            raise RuntimeError(
                "The requested backup-controller account already exists outside managed enrollment."
            )
        if state_file.is_file():
            managed_state = self.read_json(state_file)
            if managed_state.get("managed_by") != "rbf-backup-pull-enrollment" or (
                managed_state.get("username") != username
                or managed_state.get("deployment_environment")
                != response["deployment_environment"]
            ):
                raise RuntimeError("The managed backup-controller state is inconsistent.")
        if account.returncode != 0:
            subprocess.run(
                [
                    "useradd", "--system", "--no-create-home", "--home-dir", "/",
                    "--shell", "/usr/sbin/nologin", "--user-group", username,
                ],
                check=True,
                timeout=20,
            )
        password = secrets.token_urlsafe(48)
        subprocess.run(
            ["chpasswd"],
            input=f"{username}:{password}\n",
            text=True,
            check=True,
            timeout=20,
        )
        state_dir.mkdir(parents=True, exist_ok=True)
        auth_dir.mkdir(parents=True, exist_ok=True)
        dropin_dir.mkdir(parents=True, exist_ok=True)
        for directory in (state_dir, auth_dir, dropin_dir):
            subprocess.run(
                ["chown", "root:root", str(directory)], check=True, timeout=20
            )
        os.chmod(state_dir, 0o700)
        os.chmod(auth_dir, 0o755)
        os.chmod(dropin_dir, 0o755)
        for directory, mode, owner, group in (
            (chroot, "0755", "root", "root"),
            (chroot / "exports", "0750", "root", username),
            (chroot / "status", "0750", "root", username),
            (chroot / "requests", "0700", username, username),
            (chroot / "acknowledgements", "0700", username, username),
        ):
            subprocess.run(
                ["install", "-d", "-m", mode, "-o", owner, "-g", group, str(directory)],
                check=True,
                timeout=20,
            )
        self._atomic_write(
            auth_file,
            f"restrict {public_key}\n",
            # The file contains only a public key.  OpenSSH may read custom
            # AuthorizedKeysFile paths from its unprivileged auth process, so
            # a root-owned 0640 file can be rejected even with correct
            # ownership.  Keep the directory root-owned and expose only this
            # non-secret public-key file.
            0o644,
        )
        subprocess.run(["chown", "root:root", str(auth_file)], check=True, timeout=20)
        self._atomic_write(
            dropin_file,
            f"""Match User {username}
    ChrootDirectory {chroot}
    ForceCommand internal-sftp -u 0077 -d /
    AuthorizedKeysFile {auth_dir}/%u
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PubkeyAuthentication yes
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
    PermitTTY no
""",
            0o644,
        )
        subprocess.run(["chown", "root:root", str(dropin_file)], check=True, timeout=20)
        self._atomic_write(
            state_file,
            json.dumps(
                {
                    "managed_by": "rbf-backup-pull-enrollment",
                    "deployment_environment": environment,
                    "username": username,
                    "chroot": str(chroot),
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
        )
        subprocess.run(["sshd", "-t"], check=True, timeout=20)
        reload_result = subprocess.run(
            ["systemctl", "reload", "ssh.service"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        if reload_result.returncode != 0:
            subprocess.run(
                ["systemctl", "reload", "sshd.service"], check=True, timeout=20
            )

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

    @staticmethod
    def _website_host_identity() -> tuple[str, str]:
        host_key_file = Path("/etc/ssh/ssh_host_ed25519_key.pub")
        if not host_key_file.is_file() or host_key_file.is_symlink():
            raise RuntimeError("The website Ed25519 SSH host key is unavailable.")
        host_key_fields = host_key_file.read_text(encoding="ascii").split()
        if len(host_key_fields) < 2:
            raise RuntimeError("The website Ed25519 SSH host key is invalid.")
        host_key = " ".join(host_key_fields[:2])
        fingerprint_result = subprocess.run(
            ["ssh-keygen", "-lf", str(host_key_file), "-E", "sha256"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        fingerprint_fields = fingerprint_result.stdout.strip().split()
        if fingerprint_result.returncode != 0 or len(fingerprint_fields) < 2:
            raise RuntimeError("Could not fingerprint the website SSH host key.")
        return host_key, fingerprint_fields[1]

    def prepare_enrollment(self) -> dict[str, Any]:
        environment = ""
        website_host_override = ""
        website_ssh_port = 22
        env_file = self.infra_dir / ".env"
        if env_file.is_file():
            for raw_line in env_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == "DEPLOYMENT_ENVIRONMENT":
                    environment = value.strip().strip("\"'").lower()
                elif key.strip() == "BACKUP_CONTROLLER_WEBSITE_HOST":
                    website_host_override = value.strip().strip("\"'").lower()
                elif key.strip() == "BACKUP_CONTROLLER_WEBSITE_SSH_PORT":
                    try:
                        website_ssh_port = int(value.strip().strip("\"'"))
                    except ValueError as exc:
                        raise RuntimeError(
                            "BACKUP_CONTROLLER_WEBSITE_SSH_PORT must be a valid port."
                        ) from exc
        if environment not in {"test", "production"}:
            raise RuntimeError(
                "DEPLOYMENT_ENVIRONMENT must be test or production before backup enrollment."
            )
        # APP_HOSTNAME is the public HTTP name and may be shared between
        # environments.  Never use it as an SSH target implicitly: doing so
        # can enroll the test site against production's host key.
        if not website_host_override:
            raise RuntimeError(
                "BACKUP_CONTROLLER_WEBSITE_HOST must explicitly identify this "
                "environment's website SSH endpoint before backup enrollment."
            )
        website_host = website_host_override
        if not HOST_RE.fullmatch(website_host) or website_host in {
            "localhost", "127.0.0.1"
        }:
            raise RuntimeError(
                "BACKUP_CONTROLLER_WEBSITE_HOST must identify the website SSH "
                "endpoint before backup enrollment."
            )
        if not 1 <= website_ssh_port <= 65535:
            raise RuntimeError("BACKUP_CONTROLLER_WEBSITE_SSH_PORT must be between 1 and 65535.")
        website_host_key, website_host_key_fingerprint = self._website_host_identity()
        controller_username = f"rbf-backup-controller-{environment}"
        storage_directory = f"/backups/wosb/{environment}"
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
        tool_source = self.infra_dir.parent / "tools/recovery-tool/src"
        if not tool_source.is_dir() or tool_source.is_symlink():
            raise RuntimeError("The installed Recovery Tool source is unavailable.")
        archive_buffer = io.BytesIO()
        with tarfile.open(fileobj=archive_buffer, mode="w:gz") as archive:
            for path in sorted(tool_source.rglob("*.py")):
                if path.is_file() and not path.is_symlink():
                    archive.add(path, arcname=path.relative_to(tool_source))
        recovery_tool = archive_buffer.getvalue()
        if not recovery_tool or len(recovery_tool) > 1024 * 1024:
            raise RuntimeError("The embedded Recovery Tool archive is invalid.")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": REQUEST_KIND,
            "enrollment_id": secrets.token_urlsafe(32),
            "created_at": now(),
            "product_hostname": socket.gethostname(),
            "deployment_environment": environment,
            "release_version": release_version,
            "provisioner_base64": base64.b64encode(provisioner).decode("ascii"),
            "provisioner_sha256": hashlib.sha256(provisioner).hexdigest(),
            "recovery_tool_base64": base64.b64encode(recovery_tool).decode("ascii"),
            "recovery_tool_sha256": hashlib.sha256(recovery_tool).hexdigest(),
            "requested_controller_username": controller_username,
            "requested_storage_directory": storage_directory,
            "website_host": website_host,
            "website_ssh_port": website_ssh_port,
            "website_host_key": website_host_key,
            "website_host_key_fingerprint": website_host_key_fingerprint,
        }
        request = validate_request(payload)
        self._atomic_write(self.enrollment_request_file, canonical_json(request))
        self.log(
            "Created a public backup-controller enrollment request."
        )
        return {
            "enrollment_request": request,
            "enrollment_id": request["enrollment_id"],
            "enrollment_public_key": None,
        }

    @staticmethod
    def _set_env_values(path: Path, updates: dict[str, str]) -> None:
        if not path.is_file():
            raise RuntimeError("The infrastructure .env file is missing.")
        target = path.resolve(strict=True)
        if not target.is_file() or target.is_symlink():
            raise RuntimeError("The infrastructure .env target is unsafe.")
        lines = target.read_text(encoding="utf-8").splitlines()
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
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        temporary.write_text("\n".join(rendered) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)

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
        if not self.enrollment_request_file.is_file():
            raise RuntimeError(
                "Create an enrollment request before importing a response."
            )
        request = validate_request(self.read_json(self.enrollment_request_file))
        raw_response = str(self.request.get("response_json") or "")
        response = validate_response(
            parse_json_document(raw_response, "Enrollment response"),
            expected_enrollment_id=str(request["enrollment_id"]),
            expected_environment=str(request["deployment_environment"]),
        )
        expected_identity = {
            "username": request["requested_controller_username"],
            "storage_directory": request["requested_storage_directory"],
        }
        if any(response[key] != value for key, value in expected_identity.items()):
            raise RuntimeError(
                "Enrollment response identity does not match the active deployment environment."
            )
        if response["managed_server"] is not True:
            raise RuntimeError(
                "The automatic enrollment path accepts only Recovery-Tool managed controllers."
            )
        if (
            response["host"] != request["website_host"]
            or response["port"] != request["website_ssh_port"]
            or response["host_key"] != request["website_host_key"]
        ):
            raise RuntimeError("Enrollment response changed the pinned website SSH endpoint.")
        token = self.known_hosts_token(str(response["host"]), int(response["port"]))
        fingerprint = self.fingerprint_for_line(f"{token} {response['host_key']}")
        if fingerprint != response["host_key_fingerprint"]:
            raise RuntimeError(
                "The enrollment response contains a wrong SSH host-key fingerprint."
            )

        env_path = (self.infra_dir / ".env").resolve(strict=True)
        protected_paths = [env_path]
        previous = {
            path: path.read_bytes() if path.is_file() else None
            for path in protected_paths
        }
        try:
            self._install_pull_endpoint(response)
            self._set_env_values(
                env_path,
                {
                    "BACKUP_RECOVERY_ENABLED": "true",
                    "BACKUP_AGE_RECIPIENT": str(response["age_recipient"]),
                    "BACKUP_PULL_EXPORT_DIR": (
                        f"/var/lib/rbf-backup-pull/{response['deployment_environment']}/exports"
                    ),
                    "BACKUP_PULL_EXPORT_USER": str(response["username"]),
                    "BACKUP_PULL_ENROLLMENT_ID": str(response["enrollment_id"]),
                },
            )
            subprocess.run(
                [str(self.infra_dir / "scripts/deployment/install-systemd.sh")],
                check=True,
                timeout=60,
            )
        except Exception:
            for path, content in previous.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    self._atomic_write(path, content.decode("utf-8"))
            raise
        self.enrollment_request_file.unlink(missing_ok=True)
        self.log(
            "Authorized the backup-controller pull endpoint and enabled encrypted exports."
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
