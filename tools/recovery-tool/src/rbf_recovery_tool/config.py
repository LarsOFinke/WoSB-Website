from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re

from .platform_support import application_config_root


_HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{40,64}$")


@dataclass
class Profile:
    host: str = ""
    port: int = 22
    username: str = ""
    remote_directory: str = "/home/smokenougat/rbf-backups"
    destination_directory: str = str(Path.home() / "RBF-Recovery" / "Backups")
    ssh_key_path: str = ""
    age_identity_path: str = str(Path.home() / "RBF-Recovery" / "rbf-recovery-identity.txt")
    host_fingerprint: str = ""

    def normalized(self) -> "Profile":
        profile = Profile(**asdict(self))
        profile.host = profile.host.strip().rstrip(".")
        profile.username = profile.username.strip()
        profile.remote_directory = profile.remote_directory.strip().rstrip("/") or "/"
        profile.destination_directory = str(Path(profile.destination_directory).expanduser())
        profile.ssh_key_path = (
            str(Path(profile.ssh_key_path).expanduser()) if profile.ssh_key_path else ""
        )
        profile.age_identity_path = str(Path(profile.age_identity_path).expanduser())
        profile.host_fingerprint = profile.host_fingerprint.strip()
        profile.port = int(profile.port)
        return profile

    def validate(self, *, require_fingerprint: bool = False) -> None:
        profile = self.normalized()
        if not _HOST_RE.fullmatch(profile.host):
            raise ValueError("Bitte einen gültigen Hostnamen oder eine IP-Adresse eingeben.")
        if not 1 <= profile.port <= 65535:
            raise ValueError("Der SSH-Port muss zwischen 1 und 65535 liegen.")
        if not _USERNAME_RE.fullmatch(profile.username):
            raise ValueError("Der SSH-Benutzername enthält ungültige Zeichen.")
        remote = PurePosixPath(profile.remote_directory)
        if not remote.is_absolute() or any(part in {"", ".", ".."} for part in remote.parts[1:]):
            raise ValueError("Das Remote-Verzeichnis muss ein sicherer absoluter Linux-Pfad sein.")
        if not profile.destination_directory:
            raise ValueError("Bitte einen lokalen Zielordner auswählen.")
        if profile.ssh_key_path and not Path(profile.ssh_key_path).is_file():
            raise ValueError("Die ausgewählte SSH-Schlüsseldatei wurde nicht gefunden.")
        if require_fingerprint and not _FINGERPRINT_RE.fullmatch(profile.host_fingerprint):
            raise ValueError("Der SSH-Host-Key wurde noch nicht vertrauenswürdig bestätigt.")


def application_directory() -> Path:
    return application_config_root() / "RBF Recovery Tool"


def profile_path() -> Path:
    return application_directory() / "profile.json"


def load_profile() -> Profile:
    path = profile_path()
    if not path.is_file():
        return Profile()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return Profile()
        allowed = {field for field in Profile.__dataclass_fields__}
        filtered = {key: value for key, value in payload.items() if key in allowed}
        return Profile(**filtered).normalized()
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return Profile()


def save_profile(profile: Profile) -> Path:
    normalized = profile.normalized()
    normalized.validate()
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(asdict(normalized), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, path)
    return path
