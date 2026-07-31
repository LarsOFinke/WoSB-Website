from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import socket
from typing import Callable

from .config import Profile
from .verification import verify_sidecar


_BUNDLE_RE = re.compile(r"^rbf-recovery-\d{8}T\d{6}Z\.tar\.gz\.age$")


def _paramiko():
    try:
        import paramiko
    except ImportError as exc:
        raise RuntimeError("Die eingebettete SSH-Komponente konnte nicht geladen werden.") from exc
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
                raise RuntimeError("Der Server hat keinen SSH-Host-Key geliefert.")
            return key_fingerprint(key)
        finally:
            transport.close()


class PinnedFingerprintPolicy:
    def __init__(self, expected: str) -> None:
        self.expected = expected

    def missing_host_key(self, client, hostname, key) -> None:
        actual = key_fingerprint(key)
        if actual != self.expected:
            raise _paramiko().SSHException(
                f"SSH-Host-Key abgelehnt: erwartet {self.expected}, erhalten {actual}"
            )


def _remote_directory(value: str) -> str:
    path = PurePosixPath(value)
    if not path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts[1:]):
        raise RuntimeError("Das konfigurierte Remote-Verzeichnis ist unsicher.")
    return path.as_posix()


def connect(profile: Profile, password: str = ""):
    profile = profile.normalized()
    profile.validate(require_fingerprint=True)
    paramiko = _paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(PinnedFingerprintPolicy(profile.host_fingerprint))
    key_filename = profile.ssh_key_path or None
    client.connect(
        hostname=profile.host,
        port=profile.port,
        username=profile.username,
        password=password or None,
        passphrase=password or None,
        key_filename=key_filename,
        allow_agent=True,
        look_for_keys=not bool(key_filename),
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    return client


def latest_remote_bundle(sftp, remote_directory: str):
    remote_directory = _remote_directory(remote_directory)
    attributes = sftp.listdir_attr(remote_directory)
    names = {item.filename for item in attributes}
    candidates = [
        item for item in attributes
        if _BUNDLE_RE.fullmatch(item.filename) and f"{item.filename}.sha256" in names
    ]
    if not candidates:
        raise RuntimeError(
            "Im Remote-Verzeichnis wurde kein vollständiges Recovery-Bundle gefunden."
        )
    candidates.sort(key=lambda item: (item.st_mtime, item.filename), reverse=True)
    selected = candidates[0]
    root = PurePosixPath(remote_directory)
    return root / selected.filename, selected.st_size


def download_latest(
    profile: Profile,
    *,
    password: str = "",
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    profile = profile.normalized()
    profile.validate(require_fingerprint=True)
    destination = Path(profile.destination_directory)
    destination.mkdir(parents=True, exist_ok=True)
    client = connect(profile, password=password)
    try:
        sftp = client.open_sftp()
        try:
            remote_bundle, total_size = latest_remote_bundle(sftp, profile.remote_directory)
            filename = remote_bundle.name
            local_bundle = destination / filename
            local_checksum = destination / f"{filename}.sha256"
            temporary_bundle = destination / f".{filename}.part"
            temporary_checksum = destination / f".{filename}.sha256.part"
            for temporary in (temporary_bundle, temporary_checksum):
                temporary.unlink(missing_ok=True)
            try:
                callback = None
                if progress:
                    callback = lambda transferred, total: progress(transferred, total or total_size)
                sftp.get(remote_bundle.as_posix(), str(temporary_bundle), callback=callback)
                sftp.get(f"{remote_bundle.as_posix()}.sha256", str(temporary_checksum))
                os.replace(temporary_bundle, local_bundle)
                os.replace(temporary_checksum, local_checksum)
                verify_sidecar(local_bundle)
                return local_bundle
            except Exception:
                temporary_bundle.unlink(missing_ok=True)
                temporary_checksum.unlink(missing_ok=True)
                raise
        finally:
            sftp.close()
    finally:
        client.close()
