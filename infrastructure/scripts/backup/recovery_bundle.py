#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from datetime import datetime, timezone

SCHEMA_VERSION = 1
ALLOWED_ROOTS = {"artifacts", "configuration", "system", "manifest.json"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_regular_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def build_manifest(stage: Path, postgres_name: str, files_name: str) -> None:
    file_entries = []
    for path in iter_regular_files(stage):
        relative = path.relative_to(stage).as_posix()
        if relative == "manifest.json":
            continue
        file_entries.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    metadata_path = stage / "system" / "backup-metadata.json"
    metadata: dict[str, object] = {}
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "application": metadata,
        "artifacts": {
            "postgres": f"artifacts/postgres/{postgres_name}",
            "files": f"artifacts/files/{files_name}",
            "configuration": "configuration",
        },
        "files": file_entries,
    }
    target = stage / "manifest.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(target, 0o600)


def validate_member(member: tarfile.TarInfo) -> PurePosixPath:
    path = PurePosixPath(member.name)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise RuntimeError(f"Unsafe path in recovery archive: {member.name}")
    if path.parts[0] not in ALLOWED_ROOTS:
        raise RuntimeError(f"Unexpected root path in recovery archive: {member.name}")
    if not (member.isdir() or member.isfile()):
        raise RuntimeError(f"Unsupported archive entry type: {member.name}")
    return path


def extract_safely(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, mode="r:gz") as handle:
        for member in handle.getmembers():
            relative = validate_member(member)
            target = destination.joinpath(*relative.parts)
            resolved_parent = target.parent.resolve()
            if destination.resolve() not in (resolved_parent, *resolved_parent.parents):
                raise RuntimeError(f"Archive entry escapes destination: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = handle.extractfile(member)
            if source is None:
                raise RuntimeError(f"Could not read archive entry: {member.name}")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            os.chmod(target, 0o600)


def verify_extracted(root: Path) -> dict[str, object]:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("Recovery archive has no manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("Unsupported recovery-bundle schema version")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("Recovery manifest has no file inventory")

    expected_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError("Invalid recovery-manifest file entry")
        relative = str(entry.get("path") or "")
        path = PurePosixPath(relative)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise RuntimeError(f"Unsafe manifest path: {relative}")
        target = root.joinpath(*path.parts)
        if not target.is_file():
            raise RuntimeError(f"Recovery file is missing: {relative}")
        expected_paths.add(relative)
        if "size_bytes" not in entry or target.stat().st_size != int(entry["size_bytes"]):
            raise RuntimeError(f"Recovery file size mismatch: {relative}")
        if sha256_file(target) != str(entry.get("sha256") or ""):
            raise RuntimeError(f"Recovery file checksum mismatch: {relative}")

    actual_paths = {
        path.relative_to(root).as_posix()
        for path in iter_regular_files(root)
        if path.name != "manifest.json"
    }
    if actual_paths != expected_paths:
        extra = sorted(actual_paths - expected_paths)
        missing = sorted(expected_paths - actual_paths)
        raise RuntimeError(f"Recovery inventory mismatch; extra={extra}, missing={missing}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise RuntimeError("Recovery manifest has no artifact map")
    for key in ("postgres", "files", "configuration"):
        relative = str(artifacts.get(key) or "")
        target = root / relative
        if key == "configuration":
            if not target.is_dir():
                raise RuntimeError("Recovery configuration directory is missing")
        elif not target.is_file():
            raise RuntimeError(f"Recovery {key} artifact is missing")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("create-manifest")
    manifest_parser.add_argument("stage", type=Path)
    manifest_parser.add_argument("postgres_name")
    manifest_parser.add_argument("files_name")

    extract_parser = subparsers.add_parser("extract-and-verify")
    extract_parser.add_argument("archive", type=Path)
    extract_parser.add_argument("destination", type=Path)

    verify_parser = subparsers.add_parser("verify-extracted")
    verify_parser.add_argument("destination", type=Path)

    args = parser.parse_args()
    if args.command == "create-manifest":
        build_manifest(args.stage, args.postgres_name, args.files_name)
    elif args.command == "extract-and-verify":
        extract_safely(args.archive, args.destination)
        print(json.dumps(verify_extracted(args.destination), ensure_ascii=False))
    elif args.command == "verify-extracted":
        print(json.dumps(verify_extracted(args.destination), ensure_ascii=False))


if __name__ == "__main__":
    main()
