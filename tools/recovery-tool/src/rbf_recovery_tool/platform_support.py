from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


def application_config_root() -> Path:
    """Return the per-user configuration root without requiring platformdirs."""
    if os.name == "nt":
        configured = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        return Path(configured) if configured else Path.home() / "AppData" / "Roaming"
    configured = os.environ.get("XDG_CONFIG_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".config"


def application_data_root() -> Path:
    """Return the per-user data root without requiring platformdirs."""
    if os.name == "nt":
        configured = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return Path(configured) if configured else Path.home() / "AppData" / "Local"
    configured = os.environ.get("XDG_DATA_HOME")
    return (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".local" / "share"
    )


def open_directory(path: Path) -> None:
    """Open a directory in the native file manager without invoking a shell."""
    target = path.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(target)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        command = ["open", str(target)]
    elif shutil.which("xdg-open"):
        command = ["xdg-open", str(target)]
    elif shutil.which("gio"):
        command = ["gio", "open", str(target)]
    else:
        raise RuntimeError("Kein unterstützter Dateimanager-Aufruf wurde gefunden.")
    subprocess.Popen(  # noqa: S603 - fixed executable and argument vector, no shell
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
