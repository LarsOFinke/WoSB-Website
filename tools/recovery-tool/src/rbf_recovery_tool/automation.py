from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

from .config import load_profile
from .platform_support import application_config_root


_SERVICE_NAME = "rbf-recovery-pull.service"
_TIMER_NAME = "rbf-recovery-pull.timer"


def _systemd_user_directory() -> Path:
    return application_config_root() / "systemd" / "user"


def executable_path() -> Path:
    return Path(
        sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
    ).resolve()


def _systemd_quote(value: Path) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def install_pull_timer(calendar: str = "daily") -> tuple[Path, Path]:
    if os.name == "nt" or not shutil.which("systemctl"):
        raise RuntimeError(
            "Automatische Abrufe werden nur unter Linux mit systemd unterstützt."
        )
    profile = load_profile().normalized()
    profile.validate(require_fingerprint=True)
    if not profile.ssh_key_path:
        raise RuntimeError(
            "Für den automatischen Abruf muss ein SSH-Schlüssel im Profil liegen."
        )
    if not Path(profile.age_identity_path).is_file():
        raise RuntimeError("Die konfigurierte age-Identität wurde nicht gefunden.")

    directory = _systemd_user_directory()
    directory.mkdir(parents=True, exist_ok=True)
    service = directory / _SERVICE_NAME
    timer = directory / _TIMER_NAME
    service.write_text(
        "[Unit]\n"
        "Description=RBF encrypted recovery pull and verification\n"
        "After=network-online.target\n"
        "Wants=network-online.target\n\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"ExecStart={_systemd_quote(executable_path())} pull --quiet\n"
        "NoNewPrivileges=true\n"
        "PrivateTmp=true\n"
        "ProtectSystem=strict\n"
        "RestrictSUIDSGID=true\n"
        "LockPersonality=true\n"
        "UMask=0077\n",
        encoding="utf-8",
    )
    timer.write_text(
        "[Unit]\nDescription=Daily RBF recovery bundle pull\n\n"
        "[Timer]\n"
        f"OnCalendar={calendar}\n"
        "Persistent=true\n"
        "RandomizedDelaySec=15m\n\n"
        "[Install]\nWantedBy=timers.target\n",
        encoding="utf-8",
    )
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", _TIMER_NAME], check=True)
    return service, timer


def remove_pull_timer() -> None:
    if shutil.which("systemctl"):
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", _TIMER_NAME],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    directory = _systemd_user_directory()
    for name in (_SERVICE_NAME, _TIMER_NAME):
        (directory / name).unlink(missing_ok=True)
    if shutil.which("systemctl"):
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
