from __future__ import annotations

import getpass
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .docker_lab import docker_is_rootless
from .platform_support import application_data_root


def _support_candidates(name: str) -> list[Path]:
    candidates = [
        Path("/usr/lib/rbf-recovery-tool") / name,
        application_data_root() / "rbf-recovery-tool" / name,
    ]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "support" / name)
    return candidates


def support_script(name: str, *, require_root_owned: bool = False) -> Path:
    for path in _support_candidates(name):
        try:
            stat = path.stat()
        except OSError:
            continue
        if not path.is_file() or path.is_symlink():
            continue
        if require_root_owned and (stat.st_uid != 0 or stat.st_mode & 0o022):
            continue
        return path.resolve()
    qualifier = "rootgeschütztes " if require_root_owned else ""
    raise RuntimeError(f"Kein {qualifier}Hilfsskript gefunden: {name}")


def setup_rootless_lab(executable: Path) -> None:
    if os.name == "nt" or sys.platform == "darwin":
        raise RuntimeError(
            "Das automatische Rootless-Docker-Setup ist nur für Linux vorgesehen."
        )
    if docker_is_rootless():
        setup = support_script("Setup-RbfRecoveryLab.sh")
        subprocess.run([str(setup), str(executable)], check=True)
        return
    pkexec = shutil.which("pkexec")
    if not pkexec:
        raise RuntimeError(
            "PolicyKit/pkexec fehlt. Installiere das Debian-Paket oder führe die "
            "Docker-Provisionierung einmalig administrativ aus."
        )
    provisioner = support_script("Provision-RbfRecoveryLab.sh", require_root_owned=True)
    subprocess.run(
        [pkexec, str(provisioner), "--user", getpass.getuser()],
        check=True,
        timeout=1800,
    )
    setup = support_script("Setup-RbfRecoveryLab.sh")
    subprocess.run([str(setup), str(executable)], check=True, timeout=1800)
