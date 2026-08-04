#!/usr/bin/env python3
"""Safely extract and verify an RBF compiled deployment artifact."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
from typing import Any, NoReturn

INSTALLER_SCHEMA = 2
MAX_FILES = 10_000
MAX_EXPANDED_BYTES = 2 * 1024 * 1024 * 1024


def fail(message: str) -> NoReturn:
    raise SystemExit(f"[artifact] {message}")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def safe_path(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts or "." in path.parts:
        fail(f"Unsafe artifact path: {raw!r}")
    if any(not part or "\x00" in part for part in path.parts):
        fail(f"Unsafe artifact path: {raw!r}")
    return path


def load_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        fail(f"Invalid {label}: {exception}")
    if not isinstance(value, dict):
        fail(f"Invalid {label}: expected an object")
    return value


def validate_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest.get("schema_version") != 2 or manifest.get("kind") != "rbf-compiled-release":
        fail("Unsupported artifact manifest")
    minimum = manifest.get("minimum_installer_schema")
    if not isinstance(minimum, int) or minimum > INSTALLER_SCHEMA:
        fail("Artifact requires a newer installer")
    version = manifest.get("version")
    if not isinstance(version, str) or not version or any(character not in "0123456789." for character in version):
        fail("Artifact version is invalid")
    records = manifest.get("files")
    if not isinstance(records, list) or not records or len(records) > MAX_FILES:
        fail("Artifact inventory is invalid")
    inventory: dict[str, dict[str, Any]] = {}
    total = 0
    for record in records:
        if not isinstance(record, dict):
            fail("Artifact inventory is invalid")
        relative = safe_path(str(record.get("path") or "")).as_posix()
        size = record.get("size_bytes")
        checksum = record.get("sha256")
        if not relative.startswith("payload/") or relative in inventory:
            fail("Artifact inventory mismatch")
        if not isinstance(size, int) or size < 0:
            fail("Artifact inventory is invalid")
        if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            fail("Artifact inventory is invalid")
        total += size
        inventory[relative] = record
    if total > MAX_EXPANDED_BYTES:
        fail("Artifact expands beyond the supported size limit")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        fail("Artifact payload declaration is missing")
    if artifacts.get("api") != "payload/artifacts/rbf-api.jar":
        fail("Artifact API payload declaration is invalid")
    if artifacts.get("frontend") != "payload/artifacts/frontend":
        fail("Artifact frontend payload declaration is invalid")
    return inventory


def parse_sums(data: bytes) -> dict[str, str]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exception:
        fail(f"Invalid SHA256SUMS: {exception}")
    values: dict[str, str] = {}
    for line in lines:
        parts = line.split("  ", 1)
        if len(parts) != 2:
            fail("Invalid SHA256SUMS entry")
        checksum, raw = parts
        relative = safe_path(raw).as_posix()
        if relative in values or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            fail("Invalid SHA256SUMS entry")
        values[relative] = checksum
    return values


def verify_artifact(archive: Path, destination: Path) -> dict[str, Any]:
    if not archive.is_file() or archive.is_symlink():
        fail(f"Artifact is missing or unsafe: {archive}")
    if destination.exists() and any(destination.iterdir()):
        fail(f"Extraction directory is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(archive, mode="r:gz") as bundle:
            members = bundle.getmembers()
            if len(members) > MAX_FILES * 2:
                fail("Artifact contains too many archive entries")
            by_name: dict[str, tarfile.TarInfo] = {}
            expanded = 0
            for member in members:
                relative = safe_path(member.name).as_posix()
                if relative in by_name:
                    fail(f"Duplicate artifact path: {relative}")
                if not (member.isdir() or member.isfile()):
                    fail("Links and special files are forbidden")
                if member.size < 0:
                    fail("Artifact contains an invalid file size")
                expanded += member.size
                by_name[relative] = member
            if expanded > MAX_EXPANDED_BYTES:
                fail("Artifact expands beyond the supported size limit")
            manifest_member = by_name.get("manifest.json")
            sums_member = by_name.get("SHA256SUMS")
            if manifest_member is None or not manifest_member.isfile() or manifest_member.size > 4 * 1024 * 1024:
                fail("Artifact manifest is missing or too large")
            if sums_member is None or not sums_member.isfile() or sums_member.size > 4 * 1024 * 1024:
                fail("Artifact checksum inventory is missing or too large")
            manifest_stream = bundle.extractfile(manifest_member)
            sums_stream = bundle.extractfile(sums_member)
            if manifest_stream is None or sums_stream is None:
                fail("Artifact metadata cannot be read")
            manifest_bytes = manifest_stream.read()
            sums_bytes = sums_stream.read()
            manifest = load_json(manifest_bytes, "manifest.json")
            inventory = validate_manifest(manifest)
            sums = parse_sums(sums_bytes)
            expected_files = set(inventory) | {"manifest.json", "SHA256SUMS"}
            archive_files = {name for name, member in by_name.items() if member.isfile()}
            if archive_files != expected_files:
                fail("Artifact inventory mismatch")
            expected_sums = {path: str(record["sha256"]) for path, record in inventory.items()}
            expected_sums["manifest.json"] = hashlib.sha256(manifest_bytes).hexdigest()
            if sums != expected_sums:
                fail("Artifact checksum inventory mismatch")

            for member in sorted(members, key=lambda item: (len(PurePosixPath(item.name).parts), item.name)):
                relative = safe_path(member.name)
                target = destination.joinpath(*relative.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    os.chmod(target, member.mode & 0o755 or 0o755)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = bundle.extractfile(member)
                if stream is None:
                    fail(f"Artifact member cannot be read: {relative}")
                with target.open("xb") as output:
                    shutil.copyfileobj(stream, output, 1024 * 1024)
                os.chmod(target, member.mode & 0o755 or 0o600)
    except (tarfile.TarError, OSError) as exception:
        fail(f"Artifact extraction failed: {exception}")

    actual_files = {
        path.relative_to(destination).as_posix(): path
        for path in destination.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if set(actual_files) != expected_files:
        fail("Artifact inventory mismatch")
    for relative, record in inventory.items():
        target = actual_files[relative]
        if target.stat().st_size != record["size_bytes"] or digest(target) != record["sha256"]:
            fail(f"Artifact checksum mismatch: {relative}")
    if digest(actual_files["manifest.json"]) != sums["manifest.json"]:
        fail("Artifact checksum mismatch: manifest.json")
    if not (destination / "payload/artifacts/rbf-api.jar").is_file():
        fail("Compiled Spring API is missing")
    if not (destination / "payload/artifacts/frontend/index.html").is_file():
        fail("Compiled frontend is missing")
    return manifest


def main() -> None:
    if len(sys.argv) != 3:
        fail("Usage: verify-artifact.py ARTIFACT EXTRACTION_DIRECTORY")
    manifest = verify_artifact(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    print(json.dumps(manifest, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
