from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any


TARGETS = ("test", "production")
TARGET_LABELS = {"test": "Test", "production": "Production"}
CONFIG_SCHEMA_VERSION = 2
_HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{40,64}$")


def target_label(target: str) -> str:
    return TARGET_LABELS.get(target, target)


@dataclass
class Profile:
    host: str = ""
    port: int = 22
    username: str = ""
    remote_directory: str = "/data"
    destination_directory: str = ""
    ssh_key_path: str = ""
    age_identity_path: str = ""
    host_fingerprint: str = ""
    enrollment_id: str = ""

    @classmethod
    def defaults(cls, target: str) -> "Profile":
        if target not in TARGETS:
            raise ValueError(f"Unknown recovery target: {target}")
        root = Path.home() / "RBF-Recovery" / target
        return cls(
            destination_directory=str(root / "Backups"),
            ssh_key_path=str(root / "rbf-recovery-readonly-ed25519"),
            age_identity_path=str(root / "rbf-recovery-identity.txt"),
        )

    def normalized(self) -> "Profile":
        profile = Profile(**asdict(self))
        profile.host = profile.host.strip().rstrip(".")
        profile.username = profile.username.strip()
        profile.remote_directory = profile.remote_directory.strip().rstrip("/") or "/"
        profile.destination_directory = str(Path(profile.destination_directory).expanduser())
        profile.ssh_key_path = str(Path(profile.ssh_key_path).expanduser()) if profile.ssh_key_path else ""
        profile.age_identity_path = str(Path(profile.age_identity_path).expanduser()) if profile.age_identity_path else ""
        profile.host_fingerprint = profile.host_fingerprint.strip()
        profile.enrollment_id = profile.enrollment_id.strip()
        profile.port = int(profile.port)
        return profile

    def validate(
        self,
        *,
        require_fingerprint: bool = False,
        require_files: bool = False,
    ) -> None:
        profile = self.normalized()
        if not _HOST_RE.fullmatch(profile.host):
            raise ValueError("Enter a valid backup host name or IP address.")
        if not 1 <= profile.port <= 65535:
            raise ValueError("The SSH port must be between 1 and 65535.")
        if not _USERNAME_RE.fullmatch(profile.username):
            raise ValueError("The SSH username contains invalid characters.")
        remote = PurePosixPath(profile.remote_directory)
        if not remote.is_absolute() or any(part in {"", ".", ".."} for part in remote.parts[1:]):
            raise ValueError("The remote directory must be a safe absolute path.")
        if not profile.destination_directory:
            raise ValueError("Choose a local destination directory.")
        if profile.ssh_key_path and not Path(profile.ssh_key_path).is_file():
            raise ValueError("The configured SSH key file was not found.")
        if require_files and not profile.ssh_key_path:
            raise ValueError("A private read-only SSH key is required for recovery pulls.")
        if require_files and not profile.age_identity_path:
            raise ValueError("A private age identity is required for recovery pulls.")
        if require_files and not Path(profile.age_identity_path).is_file():
            raise ValueError("The configured age identity file was not found.")
        if require_fingerprint and not _FINGERPRINT_RE.fullmatch(profile.host_fingerprint):
            raise ValueError("The SSH host key has not been pinned and confirmed.")


@dataclass
class RecoveryConfig:
    active_target: str = "test"
    profiles: dict[str, Profile] = field(default_factory=dict)
    migrated_legacy: bool = False

    def profile(self, target: str | None = None) -> Profile:
        selected = target or self.active_target
        if selected not in TARGETS:
            raise ValueError(f"Unknown recovery target: {selected}")
        return self.profiles.get(selected, Profile.defaults(selected)).normalized()


def application_config_root() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home()))
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def application_directory() -> Path:
    return application_config_root() / "RBF Recovery Tool"


def config_path() -> Path:
    return application_directory() / "profiles.json"


def legacy_profile_path() -> Path:
    return application_directory() / "profile.json"


def profile_path() -> Path:
    """Compatibility name for callers that need the shared profile location."""
    return config_path()


def _profile(value: object, target: str) -> Profile:
    if not isinstance(value, dict):
        return Profile.defaults(target)
    allowed = set(Profile.__dataclass_fields__)
    filtered = {key: item for key, item in value.items() if key in allowed}
    try:
        return Profile(**filtered).normalized()
    except (TypeError, ValueError):
        return Profile.defaults(target)


def load_config() -> RecoveryConfig:
    path = config_path()
    if not path.is_file() and legacy_profile_path().is_file():
        path = legacy_profile_path()
    if not path.is_file():
        return RecoveryConfig()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return RecoveryConfig()
    if not isinstance(payload, dict):
        return RecoveryConfig()
    if payload.get("schema_version") == CONFIG_SCHEMA_VERSION:
        active = str(payload.get("active_target") or "test")
        if active not in TARGETS:
            active = "test"
        raw_profiles = payload.get("profiles")
        profiles = {
            target: _profile(raw_profiles.get(target), target)
            for target in TARGETS
            if isinstance(raw_profiles, dict) and isinstance(raw_profiles.get(target), dict)
        }
        return RecoveryConfig(active_target=active, profiles=profiles)
    # The deleted pre-Spring client stored one unlabelled profile. Importing it
    # as test is deliberate: an old profile must never silently become production.
    allowed = set(Profile.__dataclass_fields__) - {"enrollment_id"}
    legacy = {key: value for key, value in payload.items() if key in allowed}
    if legacy:
        return RecoveryConfig(
            active_target="test",
            profiles={"test": _profile(legacy, "test")},
            migrated_legacy=True,
        )
    return RecoveryConfig()


def save_config(config: RecoveryConfig) -> Path:
    if config.active_target not in TARGETS:
        raise ValueError(f"Unknown recovery target: {config.active_target}")
    payload: dict[str, Any] = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "active_target": config.active_target,
        "profiles": {
            target: asdict(config.profiles[target].normalized())
            for target in TARGETS
            if target in config.profiles
        },
    }
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, path)
    return path


def load_profile(target: str | None = None) -> Profile:
    config = load_config()
    return config.profile(target)


def save_profile(profile: Profile, target: str, *, activate: bool = True) -> Path:
    if target not in TARGETS:
        raise ValueError(f"Unknown recovery target: {target}")
    normalized = profile.normalized()
    normalized.validate()
    config = load_config()
    config.profiles[target] = normalized
    if activate:
        config.active_target = target
    return save_config(config)
