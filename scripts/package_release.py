#!/usr/bin/env python3
"""Create a deterministic, runtime-data-free release archive."""

from __future__ import annotations

import argparse
import hashlib
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {
    ".git",
    ".github-cache",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".venv-build",
    ".vite",
    "__pycache__",
    "build",
    "coverage",
    "data",
    "dist",
    "htmlcov",
    "node_modules",
    "release",
    "venv",
}
EXCLUDED_NAMES = {
    ".coverage",
    ".DS_Store",
    ".env",
    "first-run-credentials.txt",
}
EXCLUDED_SUFFIXES = {
    ".AppImage",
    ".agekey",
    ".db",
    ".deb",
    ".dll",
    ".dylib",
    ".exe",
    ".jks",
    ".key",
    ".keystore",
    ".msi",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".rpm",
    ".sha256",
    ".so",
    ".sqlite",
    ".sqlite3",
    ".tar",
    ".tgz",
    ".zip",
}
EXCLUDED_NAME_SUFFIXES = (".tar.gz",)
EXCLUDED_RELATIVE_PREFIXES = (
    Path("frontend/src/locales/generated"),
)


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative.parts):
        return False
    if any(relative == prefix or prefix in relative.parents for prefix in EXCLUDED_RELATIVE_PREFIXES):
        # The authored SVG demo uploads are the only release-safe upload fixtures.
        if relative.parts[:3] == ("backend", "storage", "uploads"):
            return relative.parts[:4] == ("backend", "storage", "uploads", "demo") and path.suffix == ".svg"
        return False
    if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name.startswith(".env") and not path.name.endswith(".example"):
        return False
    if path.name.endswith(EXCLUDED_NAME_SUFFIXES):
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=(ROOT / "VERSION").read_text(encoding="utf-8").strip())
    parser.add_argument("--output-dir", type=Path, default=ROOT.parent)
    args = parser.parse_args()

    source_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if args.version != source_version:
        raise SystemExit(f"Requested version {args.version} does not match VERSION {source_version}.")

    archive_name = f"royal-blackwater-fleet-{args.version}.zip"
    archive = args.output_dir / archive_name
    top = f"royal-blackwater-fleet-{args.version}"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and included(path))
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            relative = path.relative_to(ROOT)
            info = zipfile.ZipInfo(f"{top}/{relative.as_posix()}", date_time=(2026, 1, 1, 0, 0, 0))
            mode = path.stat().st_mode
            executable = bool(mode & stat.S_IXUSR)
            info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(archive)
    print(checksum)
    print(digest)


if __name__ == "__main__":
    main()
