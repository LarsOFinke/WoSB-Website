#!/usr/bin/env python3
"""Validate untrusted website uploads and commit them into protected storage."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time


MANIFEST_RE = re.compile(r"^rbf-backup-set-\d{8}T\d{6}Z-\d+\.json$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
REQUIRED_ARTIFACTS = {"files", "postgres", "recovery", "verification"}
MAX_MANIFEST_BYTES = 128 * 1024
MAX_PROOF_BYTES = 128 * 1024
MAX_ARTIFACT_BYTES = 100 * 1024**3
MAX_SET_BYTES = 200 * 1024**3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path: Path, *, maximum: int) -> None:
    details = path.lstat()
    if not path.is_file() or path.is_symlink() or details.st_nlink != 1:
        raise RuntimeError(f"Not an isolated regular upload: {path.name}")
    if details.st_size < 1 or details.st_size > maximum:
        raise RuntimeError(f"Upload size is outside the accepted boundary: {path.name}")


def safe_name(value: object) -> str:
    name = str(value or "")
    if not SAFE_NAME_RE.fullmatch(name) or name.endswith(".part"):
        raise RuntimeError("Backup manifest contains an unsafe filename.")
    return name


def sidecar_digest(path: Path, filename: str) -> str:
    regular(path, maximum=4096)
    fields = path.read_text(encoding="ascii").strip().split()
    digest = fields[0].lower() if fields else ""
    if not SHA256_RE.fullmatch(digest):
        raise RuntimeError(f"Invalid checksum sidecar: {path.name}")
    if len(fields) > 1 and fields[-1].lstrip("*") != filename:
        raise RuntimeError(f"Checksum sidecar names another file: {path.name}")
    return digest


def artifact_records(payload: dict[str, object]) -> list[dict[str, object]]:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != REQUIRED_ARTIFACTS:
        raise RuntimeError("A managed backup set must contain files, PostgreSQL, verification, and recovery artifacts.")
    records: list[dict[str, object]] = []
    for artifact_type, value in artifacts.items():
        if not isinstance(value, dict):
            raise RuntimeError(f"Invalid artifact record: {artifact_type}")
        records.append(value)
        metadata = value.get("restore_metadata")
        if metadata is not None:
            if artifact_type != "postgres" or not isinstance(metadata, dict):
                raise RuntimeError("Invalid restore-metadata binding.")
            records.append(metadata)
    return records


def validate_report(incoming: Path, payload: dict[str, object]) -> None:
    verification = payload["artifacts"]["verification"]  # type: ignore[index]
    report_path = incoming / safe_name(verification.get("filename"))
    if report_path.stat().st_size > MAX_PROOF_BYTES:
        raise RuntimeError("Recovery verification report is too large.")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("schema_version") != 2:
        raise RuntimeError("Recovery verification report is unsupported.")
    if report.get("mode") != "preflight" or report.get("status") != "passed" or report.get("recoverable") is not True:
        raise RuntimeError("Recovery verification did not pass.")
    checks = report.get("checks")
    passed = {
        str(check.get("name"))
        for check in checks
        if isinstance(check, dict) and check.get("status") == "passed"
    } if isinstance(checks, list) else set()
    required = {
        "dump_inventory", "staging_database_restore", "flyway_validation",
        "application_readiness", "preflight_cleanup",
    }
    if not required.issubset(passed):
        raise RuntimeError("Recovery verification is missing required checks.")


def load_set(incoming: Path, manifest: Path) -> tuple[dict[str, object], list[Path], str]:
    regular(manifest, maximum=MAX_MANIFEST_BYTES)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or payload.get("committed") is not True:
        raise RuntimeError("Backup-set manifest is unsupported.")
    if payload.get("consistency") not in {"application-quiesced", "no-running-api"}:
        raise RuntimeError("Backup set has no production-consistent database snapshot.")
    manifest_digest = sha256_file(manifest)
    if sidecar_digest(incoming / f"{manifest.name}.sha256", manifest.name) != manifest_digest:
        raise RuntimeError("Backup-set manifest checksum does not match.")

    sources: list[Path] = []
    seen: set[str] = set()
    total = 0
    for record in artifact_records(payload):
        name = safe_name(record.get("filename"))
        if name in seen or name in {manifest.name, f"{manifest.name}.sha256"}:
            raise RuntimeError("Backup set contains duplicate filenames.")
        seen.add(name)
        source = incoming / name
        regular(source, maximum=MAX_ARTIFACT_BYTES)
        size = int(record.get("size_bytes", -1))
        digest = str(record.get("sha256") or "")
        if source.stat().st_size != size or not SHA256_RE.fullmatch(digest):
            raise RuntimeError(f"Backup artifact metadata mismatch: {name}")
        if sha256_file(source) != digest:
            raise RuntimeError(f"Backup artifact checksum mismatch: {name}")
        sidecar = incoming / f"{name}.sha256"
        if sidecar_digest(sidecar, name) != digest:
            raise RuntimeError(f"Backup artifact sidecar mismatch: {name}")
        sources.extend((source, sidecar))
        total += size
    if total > MAX_SET_BYTES:
        raise RuntimeError("Backup set exceeds the managed storage boundary.")
    validate_report(incoming, payload)
    sources.extend((manifest.with_name(f"{manifest.name}.sha256"), manifest))
    return payload, sources, manifest_digest


def protected_copy(source: Path, destination: Path, group_id: int) -> None:
    if destination.exists():
        raise FileExistsError(destination.name)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        temporary = Path(handle.name)
        with source.open("rb") as reader:
            shutil.copyfileobj(reader, handle, length=1024 * 1024)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.chown(temporary, 0, group_id)
        os.chmod(temporary, 0o640)
        if sha256_file(temporary) != sha256_file(source):
            raise RuntimeError(f"Upload changed while being committed: {source.name}")
        os.link(temporary, destination, follow_symlinks=False)
    finally:
        temporary.unlink(missing_ok=True)


def receipt(receipts: Path, manifest: str, payload: dict[str, object], group_id: int) -> None:
    target = receipts / f"{manifest}.receipt.json"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=receipts, delete=False) as handle:
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.chown(temporary, 0, group_id)
    os.chmod(temporary, 0o440)
    os.replace(temporary, target)


def process_manifest(
    incoming: Path,
    committed: Path,
    receipts: Path,
    manifest: Path,
    read_group_id: int,
    upload_group_id: int,
) -> None:
    created: list[Path] = []
    try:
        _payload, sources, manifest_digest = load_set(incoming, manifest)
        existing_receipt = receipts / f"{manifest.name}.receipt.json"
        if existing_receipt.is_file():
            prior = json.loads(existing_receipt.read_text(encoding="utf-8"))
            if prior.get("status") == "accepted" and prior.get("manifest_sha256") == manifest_digest:
                for source in sources:
                    source.unlink(missing_ok=True)
                return
        for source in sources:
            destination = committed / source.name
            protected_copy(source, destination, read_group_id)
            created.append(destination)
        receipt(receipts, manifest.name, {
            "schema_version": 1,
            "kind": "rbf-backup-ingest-receipt",
            "status": "accepted",
            "manifest": manifest.name,
            "manifest_sha256": manifest_digest,
            "committed_at": int(time.time()),
        }, upload_group_id)
        for source in sources:
            source.unlink(missing_ok=True)
    except Exception as exc:
        for path in created:
            path.unlink(missing_ok=True)
        receipt(receipts, manifest.name, {
            "schema_version": 1,
            "kind": "rbf-backup-ingest-receipt",
            "status": "rejected",
            "manifest": manifest.name,
            "detail": str(exc)[:500],
        }, upload_group_id)
        manifest.unlink(missing_ok=True)
        manifest.with_name(f"{manifest.name}.sha256").unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("incoming", type=Path)
    parser.add_argument("committed", type=Path)
    parser.add_argument("receipts", type=Path)
    parser.add_argument("--read-group-id", type=int, required=True)
    parser.add_argument("--upload-group-id", type=int, required=True)
    args = parser.parse_args()
    for manifest in sorted(args.incoming.glob("rbf-backup-set-*.json")):
        if MANIFEST_RE.fullmatch(manifest.name):
            process_manifest(
                args.incoming,
                args.committed,
                args.receipts,
                manifest,
                args.read_group_id,
                args.upload_group_id,
            )
    cutoff = time.time() - 2 * 86400
    for candidate in args.incoming.iterdir():
        try:
            if candidate.is_file() and not candidate.is_symlink() and candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
