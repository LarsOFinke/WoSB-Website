#!/usr/bin/env python3
"""Validate an immutable selected release before retrying its activation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify(root: Path, version: str, manifest_path: Path, checksum: str) -> tuple[str, bool]:
    release = root / "releases" / version
    record_path = root / "shared/deployments" / f"{version}.json"
    if release.is_symlink() or not record_path.is_file() or record_path.is_symlink():
        raise ValueError("Selected release or deployment metadata is unsafe or missing")
    record = json.loads(record_path.read_text())
    if record.get("state") not in {"failed", "activating"}:
        raise ValueError("Immutable release is already active; only failed/interrupted activations can resume")
    if (root / "current").resolve() != release or record.get("current_release") != str(release):
        raise ValueError("Selected release does not match deployment metadata")
    archive = root / "shared/release-artifacts" / f"rbf-deployment-{version}.tar.gz"
    if archive.is_symlink() or digest(archive) != checksum:
        raise ValueError("Retry requires the exact original artifact; use a new version for changed content")
    manifest = json.loads(manifest_path.read_text())
    if manifest != json.loads((release / ".release-manifest.json").read_text()):
        raise ValueError("Retry manifest differs from the selected release")
    for entry in manifest["files"]:
        relative = Path(entry["path"]).relative_to("payload")
        path = release / relative
        if not path.resolve().is_relative_to(release) or path.is_symlink() or digest(path) != entry["sha256"]:
            raise ValueError("Selected release payload changed; repair from the verified artifact before retrying")
    previous = record.get("previous_release") or ""
    migration = record.get("host_nginx_migration") is True
    if previous:
        previous_path = Path(previous)
        if (previous_path.parent != root / "releases" or previous_path == release
                or previous_path.is_symlink() or not previous_path.is_dir()):
            raise ValueError("Original previous release is missing or unsafe")
        migration = migration or not (previous_path / "infrastructure/nginx/host-site.conf").is_file()
    if migration:
        for key in ("rollback_postgres", "rollback_files"):
            backup = Path(record.get(key) or "")
            if not backup.is_file() or not Path(f"{backup}.sha256").is_file():
                raise ValueError("Original coordinated migration backup is unavailable; recover it before retrying")
    return previous, migration


if __name__ == "__main__":
    try:
        previous, migration = verify(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"[resume] {error}") from error
    print(previous, end="\0")
    print("true" if migration else "false", end="\0")
