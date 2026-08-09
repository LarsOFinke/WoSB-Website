from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

from .config import application_config_root, load_profile


_SERVICE_NAME = "rbf-recovery-pull.service"
_TIMER_NAME = "rbf-recovery-pull.timer"


def _systemd_user_directory() -> Path:
    return application_config_root() / "systemd" / "user"


def executable_path() -> Path:
    return Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]).resolve()


def _systemd_quote(value: Path) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def install_pull_timer(target: str, calendar: str = "daily") -> tuple[Path, Path]:
    if os.name == "nt" or not shutil.which("systemctl"):
        raise RuntimeError("Automatic pulls are supported only on Linux with systemd.")
    profile = load_profile(target).normalized()
    profile.validate(require_fingerprint=True, require_files=True)
    directory = _systemd_user_directory()
    directory.mkdir(parents=True, exist_ok=True)
    service = directory / f"{target}-{_SERVICE_NAME}"
    timer = directory / f"{target}-{_TIMER_NAME}"
    service.write_text(
        "[Unit]\n"
        f"Description=RBF {target} recovery pull and verification\n"
        "After=network-online.target\nWants=network-online.target\n\n"
        "[Service]\nType=oneshot\n"
        f"ExecStart={_systemd_quote(executable_path())} pull --target {target} --quiet\n"
        "NoNewPrivileges=true\nPrivateTmp=true\nProtectSystem=strict\n"
        "RestrictSUIDSGID=true\nLockPersonality=true\nUMask=0077\n",
        encoding="utf-8",
    )
    timer.write_text(
        "[Unit]\n"
        f"Description=RBF {target} recovery pull\n\n"
        "[Timer]\n"
        f"OnCalendar={calendar}\nPersistent=true\nRandomizedDelaySec=15m\n\n"
        "[Install]\nWantedBy=timers.target\n",
        encoding="utf-8",
    )
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", timer.name], check=True)
    return service, timer


def remove_pull_timer(target: str) -> None:
    if shutil.which("systemctl"):
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", f"{target}-{_TIMER_NAME}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    directory = _systemd_user_directory()
    for name in (f"{target}-{_SERVICE_NAME}", f"{target}-{_TIMER_NAME}"):
        (directory / name).unlink(missing_ok=True)
    if shutil.which("systemctl"):
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
