from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import stat
from typing import Callable

from .config import Profile


_BUNDLE_RE = re.compile(r"^rbf-recovery-\d{8}T\d{6}Z\.tar\.gz\.age$")
_SET_RE = re.compile(r"^rbf-backup-set-\d{8}T\d{6}Z-\d+\.json$")
_REPORT_RE = re.compile(r"^rbf-postgres-preflight-\d{8}T\d{6}Z-\d+\.json$")
_MAX_SET_BYTES = 128 * 1024
_MAX_REPORT_BYTES = 128 * 1024
_MAX_SIDECAR_BYTES = 4096
_REQUIRED_PREFLIGHTS = {
    "dump_inventory",
    "staging_database_restore",
    "flyway_validation",
    "application_readiness",
    "preflight_cleanup",
}


def _paramiko():
    try:
        import paramiko
    except ImportError as exc:
        raise RuntimeError(
            "The SSH component is not installed. Install the recovery-tool runtime dependencies."
        ) from exc
    return paramiko


def key_fingerprint(key) -> str:
    digest = hashlib.sha256(key.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def fetch_host_fingerprint(profile: Profile, timeout: int = 15) -> str:
    profile = profile.normalized()
    profile.validate()
    paramiko = _paramiko()
    with socket.create_connection((profile.host, profile.port), timeout=timeout) as connection:
        transport = paramiko.Transport(connection)
        try:
            transport.start_client(timeout=timeout)
            key = transport.get_remote_server_key()
            if key is None:
                raise RuntimeError("The SSH server did not provide a host key.")
            return key_fingerprint(key)
        finally:
            transport.close()


class PinnedFingerprintPolicy:
    def __init__(self, expected: str) -> None:
        self.expected = expected

    def missing_host_key(self, _client, _hostname, key) -> None:
        actual = key_fingerprint(key)
        if actual != self.expected:
            raise _paramiko().SSHException(
                f"SSH host key rejected: expected {self.expected}, received {actual}"
            )


def _remote_directory(value: str) -> str:
    path = PurePosixPath(value)
    if not path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts[1:]):
        raise RuntimeError("The configured remote directory is unsafe.")
    return path.as_posix()


def connect(profile: Profile, password: str = ""):
    profile = profile.normalized()
    profile.validate(require_fingerprint=True)
    paramiko = _paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(PinnedFingerprintPolicy(profile.host_fingerprint))
    key_filename = profile.ssh_key_path or None
    try:
        client.connect(
            hostname=profile.host,
            port=profile.port,
            username=profile.username,
            password=password or None,
            passphrase=password or None,
            key_filename=key_filename,
            allow_agent=not bool(key_filename),
            look_for_keys=not bool(key_filename),
            timeout=20,
            banner_timeout=20,
            auth_timeout=20,
        )
    except Exception as exc:
        client.close()
        raise RuntimeError(
            f"SSH login failed for {profile.username}@{profile.host}:{profile.port}: {exc}"
        ) from exc
    return client


def _remote_bytes(sftp, path: PurePosixPath, *, limit: int) -> bytes:
    attributes = sftp.stat(path.as_posix())
    if not stat.S_ISREG(attributes.st_mode) or attributes.st_size > limit:
        raise RuntimeError(f"Remote proof is not an allowed regular file: {path.name}")
    with sftp.open(path.as_posix(), "rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError(f"Remote proof is too large: {path.name}")
    return data


def _sidecar_digest(data: bytes, expected_filename: str) -> str:
    try:
        fields = data.decode("ascii").strip().split()
    except UnicodeDecodeError as exc:
        raise RuntimeError("Remote checksum is not ASCII encoded.") from exc
    digest = fields[0].lower() if fields else ""
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise RuntimeError("Remote checksum is invalid.")
    if len(fields) > 1 and fields[-1].lstrip("*") != expected_filename:
        raise RuntimeError("Remote checksum names a different file.")
    return digest


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verified_remote_file(sftp, root: PurePosixPath, filename: str, *, limit: int) -> bytes:
    if PurePosixPath(filename).name != filename:
        raise RuntimeError("Remote artifact filename is unsafe.")
    data = _remote_bytes(sftp, root / filename, limit=limit)
    sidecar = _remote_bytes(sftp, root / f"{filename}.sha256", limit=_MAX_SIDECAR_BYTES)
    expected = _sidecar_digest(sidecar, filename)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Remote proof has a wrong checksum: {filename}")
    return data


def _record(artifacts: object, name: str) -> dict[str, object]:
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get(name), dict):
        raise RuntimeError(f"Backup set has no {name} proof.")
    return artifacts[name]


def _validate_report(report: dict[str, object]) -> None:
    if (
        report.get("schema_version") != 2
        or report.get("mode") != "preflight"
        or report.get("status") != "passed"
        or report.get("recoverable") is not True
    ):
        raise RuntimeError("Remote backup has no successful Spring/Flyway recovery preflight.")
    checks = report.get("checks")
    passed = {
        str(check.get("name"))
        for check in checks
        if isinstance(check, dict) and check.get("status") == "passed"
    } if isinstance(checks, list) else set()
    missing = _REQUIRED_PREFLIGHTS - passed
    if missing:
        raise RuntimeError(f"Recovery preflight is missing checks: {', '.join(sorted(missing))}")


def _validate_commit_payload(
    set_payload: dict[str, object],
    report_payload: dict[str, object],
    *,
    bundle_name: str,
    bundle_size: int,
    bundle_sha256: str | None = None,
    report_name: str,
    report_size: int,
    report_sha256: str,
) -> None:
    if set_payload.get("schema_version") != 1 or set_payload.get("committed") is not True:
        raise RuntimeError("Remote backup set is not committed or is unsupported.")
    artifacts = set_payload.get("artifacts")
    recovery = _record(artifacts, "recovery")
    verification = _record(artifacts, "verification")
    if recovery.get("filename") != bundle_name or int(recovery.get("size_bytes", -1)) != bundle_size:
        raise RuntimeError("Remote backup set does not bind the offered recovery bundle.")
    if bundle_sha256 is not None and recovery.get("sha256") != bundle_sha256:
        raise RuntimeError("Recovery bundle does not match the remote commit marker.")
    if (
        verification.get("filename") != report_name
        or int(verification.get("size_bytes", -1)) != report_size
        or verification.get("sha256") != report_sha256
    ):
        raise RuntimeError("Recovery report does not match the remote commit marker.")
    _validate_report(report_payload)
    source = report_payload.get("source_artifact")
    postgres = _record(artifacts, "postgres") if isinstance(artifacts, dict) and "postgres" in artifacts else None
    if postgres is not None and isinstance(source, dict):
        for key in ("filename", "size_bytes", "sha256"):
            if source.get(key) != postgres.get(key):
                raise RuntimeError(f"Recovery report source binding mismatch: {key}")


def latest_remote_bundle(sftp, remote_directory: str):
    root = PurePosixPath(_remote_directory(remote_directory))
    attributes = sftp.listdir_attr(root.as_posix())
    by_name = {str(item.filename): item for item in attributes}
    candidates = [
        item for item in attributes
        if _SET_RE.fullmatch(str(item.filename)) and f"{item.filename}.sha256" in by_name
    ]
    candidates.sort(key=lambda item: (item.st_mtime, str(item.filename)), reverse=True)
    for candidate in candidates:
        try:
            set_name = str(candidate.filename)
            set_data = _verified_remote_file(sftp, root, set_name, limit=_MAX_SET_BYTES)
            set_payload = json.loads(set_data.decode("utf-8"))
            if not isinstance(set_payload, dict):
                raise RuntimeError("Remote backup set is not a JSON object.")
            recovery = _record(set_payload.get("artifacts"), "recovery")
            verification = _record(set_payload.get("artifacts"), "verification")
            bundle_name = str(recovery.get("filename") or "")
            report_name = str(verification.get("filename") or "")
            if not _BUNDLE_RE.fullmatch(bundle_name) or not _REPORT_RE.fullmatch(report_name):
                raise RuntimeError("Remote backup set contains unsafe filenames.")
            required = {
                bundle_name, f"{bundle_name}.sha256",
                report_name, f"{report_name}.sha256",
            }
            if not required.issubset(by_name):
                raise RuntimeError("Remote backup set is incomplete.")
            report_data = _verified_remote_file(sftp, root, report_name, limit=_MAX_REPORT_BYTES)
            report_payload = json.loads(report_data.decode("utf-8"))
            if not isinstance(report_payload, dict):
                raise RuntimeError("Remote recovery report is not a JSON object.")
            bundle_attr = by_name[bundle_name]
            _validate_commit_payload(
                set_payload,
                report_payload,
                bundle_name=bundle_name,
                bundle_size=int(bundle_attr.st_size),
                report_name=report_name,
                report_size=len(report_data),
                report_sha256=hashlib.sha256(report_data).hexdigest(),
            )
            return root / bundle_name, int(bundle_attr.st_size), root / set_name, root / report_name
        except (RuntimeError, UnicodeDecodeError, json.JSONDecodeError, OSError, TypeError, ValueError):
            continue
    raise RuntimeError("No committed bundle with a successful recovery preflight was found on the backup server.")


def download_latest(
    profile: Profile,
    *,
    password: str = "",
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    profile = profile.normalized()
    profile.validate(require_fingerprint=True, require_files=True)
    destination = Path(profile.destination_directory)
    destination.mkdir(parents=True, exist_ok=True)
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            remote_bundle, total_size, remote_set, remote_report = latest_remote_bundle(
                sftp, profile.remote_directory
            )
            remote_files = [
                remote_bundle,
                PurePosixPath(f"{remote_bundle.as_posix()}.sha256"),
                remote_report,
                PurePosixPath(f"{remote_report.as_posix()}.sha256"),
                PurePosixPath(f"{remote_set.as_posix()}.sha256"),
                remote_set,
            ]
            temporary: list[Path] = []
            completed: list[Path] = []
            try:
                for remote in remote_files:
                    local = destination / remote.name
                    partial = destination / f".{remote.name}.part"
                    partial.unlink(missing_ok=True)
                    callback = None
                    if progress and remote == remote_bundle:
                        callback = lambda transferred, total: progress(transferred, total or total_size)
                    sftp.get(remote.as_posix(), str(partial), callback=callback)
                    temporary.append(partial)
                    completed.append(local)
                for partial, local in zip(temporary, completed, strict=True):
                    os.replace(partial, local)
                local_bundle, _bundle_sidecar, local_report, _report_sidecar, _set_sidecar, local_set = completed
                _verify_local_sidecar(local_bundle)
                _verify_local_sidecar(local_report)
                _verify_local_sidecar(local_set)
                set_payload = json.loads(local_set.read_text(encoding="utf-8"))
                report_payload = json.loads(local_report.read_text(encoding="utf-8"))
                _validate_commit_payload(
                    set_payload,
                    report_payload,
                    bundle_name=local_bundle.name,
                    bundle_size=local_bundle.stat().st_size,
                    bundle_sha256=_file_digest(local_bundle),
                    report_name=local_report.name,
                    report_size=local_report.stat().st_size,
                    report_sha256=_file_digest(local_report),
                )
                return local_bundle
            except Exception:
                for partial in temporary:
                    partial.unlink(missing_ok=True)
                raise
        finally:
            sftp.close()
    finally:
        client.close()


def _verify_local_sidecar(path: Path) -> str:
    checksum = Path(f"{path}.sha256")
    if not checksum.is_file() or checksum.stat().st_size > _MAX_SIDECAR_BYTES:
        raise RuntimeError(f"Checksum sidecar is missing: {checksum.name}")
    expected = _sidecar_digest(checksum.read_bytes(), path.name)
    actual = _file_digest(path)
    if expected != actual:
        raise RuntimeError(f"Checksum mismatch: {path.name}")
    return actual


__all__ = [
    "_MAX_REPORT_BYTES",
    "_MAX_SET_BYTES",
    "_REPORT_RE",
    "_SET_RE",
    "_remote_bytes",
    "_sidecar_digest",
    "_verified_remote_file",
    "connect",
    "download_latest",
    "fetch_host_fingerprint",
    "latest_remote_bundle",
]
