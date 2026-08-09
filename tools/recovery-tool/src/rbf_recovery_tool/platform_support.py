from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


def open_directory(path: Path) -> None:
    path = path.expanduser().resolve()
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys_platform() == "darwin":
        subprocess.Popen(["open", str(path)])
    elif shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", str(path)])
    elif shutil.which("gio"):
        subprocess.Popen(["gio", "open", str(path)])
    else:
        raise RuntimeError(f"Directory: {path}")


def sys_platform() -> str:
    import sys

    return sys.platform

