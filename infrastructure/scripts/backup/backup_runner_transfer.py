from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
from typing import Any

from backup_runner_core import HOST_RE, REMOTE_RE, USER_RE, now


class BackupTransferMixin:
    def load_connection(self) -> dict[str, Any]:
        if (
            not self.config_file.is_file()
            or not self.key_file.is_file()
            or not self.known_hosts_file.is_file()
        ):
            raise RuntimeError("Configure the remote backup connection first.")
        config = self.read_json(self.config_file)
        host = str(config.get("host") or "")
        username = str(config.get("username") or "")
        remote_directory = str(config.get("remote_directory") or "")
        port = int(config.get("port") or 22)
        if (
            not 1 <= port <= 65535
            or not HOST_RE.fullmatch(host)
            or not USER_RE.fullmatch(username)
            or not REMOTE_RE.fullmatch(remote_directory)
        ):
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
            "-P",
            str(config["port"]),
            "-i",
            str(key_path or self.key_file),
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={known_hosts_file or self.known_hosts_file}",
            "-o",
            "ConnectTimeout=15",
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
            line
            for line in lines
            if any(
                marker in line.lower()
                for marker in (
                    "permission denied",
                    "no such file",
                    "failure",
                    "not found",
                    "host key verification",
                    "connection refused",
                    "connection closed",
                )
            )
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
        batch = "\n".join(
            [
                f"cd {config['remote_directory']}",
                f"put {source} {remote_part}",
                f"rename {remote_part} {remote_final}",
                f"get {remote_final} {downloaded}",
                f"rm {remote_final}",
                "quit",
                "",
            ]
        )
        try:
            result = subprocess.run(
                [
                    "sftp",
                    "-q",
                    "-b",
                    "-",
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
                raise RuntimeError(
                    f"SFTP write test failed: {self._sftp_error_detail(result)}"
                )
            if not downloaded.is_file() or downloaded.read_bytes() != payload:
                raise RuntimeError(
                    "SFTP write test failed: the downloaded test payload did not match."
                )
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
            self._atomic_write(
                self.config_file,
                json.dumps(stored, ensure_ascii=False, indent=2) + "\n",
            )
        return tested_at

    def transfer(
        self, config: dict[str, Any], backup_file: Path, artifact_type: str
    ) -> dict[str, Any]:
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
            commands.extend(
                [
                    f"put {checksum_file} {checksum_name}.part",
                    f"chmod 0640 {checksum_name}.part",
                    f"rename {checksum_name}.part {checksum_name}",
                    f"put {backup_file} {filename}.part",
                    f"chmod 0640 {filename}.part",
                    f"rename {filename}.part {filename}",
                ]
            )
        else:
            commands.extend(
                [
                    f"put {backup_file} {filename}.part",
                    f"chmod 0640 {filename}.part",
                    f"rename {filename}.part {filename}",
                    f"put {checksum_file} {checksum_name}.part",
                    f"chmod 0640 {checksum_name}.part",
                    f"rename {checksum_name}.part {checksum_name}",
                ]
            )
        if metadata_file.is_file() and metadata_checksum.is_file():
            metadata_name = metadata_file.name
            metadata_checksum_name = metadata_checksum.name
            commands.extend(
                [
                    f"put {metadata_file} {metadata_name}.part",
                    f"chmod 0640 {metadata_name}.part",
                    f"rename {metadata_name}.part {metadata_name}",
                    f"put {metadata_checksum} {metadata_checksum_name}.part",
                    f"chmod 0640 {metadata_checksum_name}.part",
                    f"rename {metadata_checksum_name}.part {metadata_checksum_name}",
                ]
            )
        commands.extend(["quit", ""])
        batch = "\n".join(commands)
        self.log(
            f"Transferring {filename} and checksum to the configured backup server."
        )
        result = subprocess.run(
            ["sftp", "-q", "-b", "-", *self.ssh_base(config)],
            input=batch,
            text=True,
            capture_output=True,
            timeout=900,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or [
                "unknown SFTP error"
            ]
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
                if (
                    hashlib.sha256(verification_copy.read_bytes()).hexdigest()
                    != hashlib.sha256(source.read_bytes()).hexdigest()
                ):
                    raise RuntimeError(
                        "The remote SFTP verification failed after upload: digest mismatch."
                    )
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
            command = [
                "/usr/bin/env",
                "bash",
                str(self.infra_dir / f"scripts/backup/{script_name}"),
            ]
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
                raise RuntimeError(
                    f"{description.capitalize()} backup creation failed."
                )
            backup_path = result_file.read_text(encoding="utf-8").strip()
            backup_file = Path(backup_path)
            if not backup_file.is_absolute():
                raise RuntimeError(
                    f"{description.capitalize()} backup returned an invalid path."
                )
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
            "--reason",
            "admin-requested",
            "--postgres-result",
            str(result_files["postgres"]),
            "--files-result",
            str(result_files["files"]),
            "--recovery-result",
            str(result_files["recovery"]),
            "--verification-result",
            str(result_files["verification"]),
            "--backup-set-result",
            str(result_files["set"]),
        ]
        if self.recovery_enabled():
            command.append("--include-recovery")
        self.log(
            "Creating one coordinated backup set and proving full recoverability before transfer."
        )
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
                raise RuntimeError(
                    "Coordinated backup or recovery verification failed."
                )
            required = ("postgres", "files", "verification", "set")
            if any(not result_files[name].is_file() for name in required):
                raise RuntimeError(
                    "The coordinated backup did not return every required artifact."
                )
            paths = {
                name: Path(result_files[name].read_text(encoding="utf-8").strip())
                for name in required
            }
            if self.recovery_enabled():
                if not result_files["recovery"].is_file():
                    raise RuntimeError(
                        "Encrypted recovery bundle was enabled but not returned."
                    )
                paths["recovery"] = Path(
                    result_files["recovery"].read_text(encoding="utf-8").strip()
                )
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
