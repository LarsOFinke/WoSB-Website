#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = 2
ALLOWED_ROOTS = {"artifacts", "configuration", "system", "manifest.json"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_files(root: Path):
    return sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def create_manifest(stage: Path, postgres_name: str, files_name: str, release_name: str) -> None:
    metadata_path = stage / "system" / "backup-metadata.json"
    application = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    entries = []
    for path in regular_files(stage):
        relative = path.relative_to(stage).as_posix()
        if relative == "manifest.json":
            continue
        entries.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "rbf-disaster-recovery-bundle",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "application": application,
        "artifacts": {
            "postgres": f"artifacts/postgres/{postgres_name}",
            "files": f"artifacts/files/{files_name}",
            "release": f"artifacts/release/{release_name}",
            "configuration": "configuration",
        },
        "files": entries,
    }
    target = stage / "manifest.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(target, 0o600)


def safe_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise RuntimeError(f"Unsafe path in recovery archive: {name}")
    if path.parts[0] not in ALLOWED_ROOTS:
        raise RuntimeError(f"Unexpected root path in recovery archive: {name}")
    return path


def extract_safely(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            relative = safe_path(member.name)
            if not (member.isdir() or member.isfile()):
                raise RuntimeError(f"Links and special entries are forbidden: {member.name}")
            target = destination.joinpath(*relative.parts)
            parent = target.parent.resolve(); root = destination.resolve()
            if root != parent and root not in parent.parents:
                raise RuntimeError(f"Archive path escapes destination: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True); continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = bundle.extractfile(member)
            if source is None: raise RuntimeError(f"Cannot read archive entry: {member.name}")
            with source, target.open("wb") as output: shutil.copyfileobj(source, output)
            os.chmod(target, 0o600)


def verify_extracted(root: Path) -> dict[str, object]:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file(): raise RuntimeError("Recovery manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("kind") != "rbf-disaster-recovery-bundle":
        raise RuntimeError("Unsupported recovery bundle")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries: raise RuntimeError("Recovery inventory is empty")
    expected: set[str] = set()
    for entry in entries:
        relative = str(entry.get("path") or ""); path = safe_path(relative)
        target = root.joinpath(*path.parts)
        if not target.is_file() or target.is_symlink(): raise RuntimeError(f"Recovery file missing: {relative}")
        if target.stat().st_size != int(entry.get("size_bytes", -1)): raise RuntimeError(f"Size mismatch: {relative}")
        if sha256_file(target) != str(entry.get("sha256") or ""): raise RuntimeError(f"Checksum mismatch: {relative}")
        expected.add(relative)
    actual = {path.relative_to(root).as_posix() for path in regular_files(root) if path.name != "manifest.json"}
    if actual != expected: raise RuntimeError(f"Inventory mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict): raise RuntimeError("Artifact map is missing")
    for key in ("postgres", "files", "release"):
        if not (root / str(artifacts.get(key) or "")).is_file(): raise RuntimeError(f"Recovery {key} artifact is missing")
    if not (root / str(artifacts.get("configuration") or "")).is_dir(): raise RuntimeError("Recovery configuration is missing")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(); commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-manifest"); create.add_argument("stage", type=Path); create.add_argument("postgres_name"); create.add_argument("files_name"); create.add_argument("release_name")
    extract = commands.add_parser("extract-and-verify"); extract.add_argument("archive", type=Path); extract.add_argument("destination", type=Path)
    verify = commands.add_parser("verify-extracted"); verify.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "create-manifest": create_manifest(args.stage, args.postgres_name, args.files_name, args.release_name)
    elif args.command == "extract-and-verify": extract_safely(args.archive, args.destination); print(json.dumps(verify_extracted(args.destination), sort_keys=True))
    else: print(json.dumps(verify_extracted(args.destination), sort_keys=True))

if __name__ == "__main__": main()
