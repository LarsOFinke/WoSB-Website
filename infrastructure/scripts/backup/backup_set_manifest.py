#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

SCHEMA_VERSION = 1
MAX_MANIFEST_BYTES = 128 * 1024
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
PRODUCTION_CONSISTENCY = frozenset({"application-quiesced", "no-running-api"})
REQUIRED_RECOVERY_CHECKS = frozenset(
    {
        "metadata_compatibility",
        "staging_database_creation",
        "postgres_import",
        "migration_and_schema_preflight",
        "secret_key_preflight",
        "application_readiness_preflight",
        "preflight_cleanup",
    }
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _checksum(path: Path) -> str:
    sidecar = Path(f"{path}.sha256")
    if not sidecar.is_file() or sidecar.is_symlink() or sidecar.stat().st_size > 4096:
        raise RuntimeError(f"Mandatory checksum is missing or invalid: {sidecar}")
    fields = sidecar.read_text(encoding="ascii").strip().split()
    expected = fields[0].lower() if fields else ""
    if not SHA_RE.fullmatch(expected):
        raise RuntimeError(f"Invalid checksum: {sidecar}")
    if len(fields) > 1 and fields[-1].lstrip("*") != path.name:
        raise RuntimeError(f"Checksum filename mismatch: {sidecar}")
    actual = sha256_file(path)
    if not hmac.compare_digest(expected, actual):
        raise RuntimeError(f"Checksum mismatch: {path}")
    return actual


def _regular(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Artifact is not a regular file: {path}")
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode):
        raise RuntimeError(f"Artifact is not a regular file: {path}")


def _artifact(root: Path, path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    _regular(path)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"Artifact is outside the infrastructure tree: {path}") from exc
    return {
        "path": relative.as_posix(),
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _checksum(path),
    }


def _read_json(path: Path, limit: int) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        raise RuntimeError(f"JSON artifact is missing or too large: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON artifact is not an object: {path}")
    return payload


def _metadata_record(root: Path, postgres: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = Path(f"{postgres}.restore.json")
    metadata_payload = _read_json(metadata, 32 * 1024)
    if int(metadata_payload.get("schema_version", -1)) != 2:
        raise RuntimeError("Only restore-metadata schema 2 may be committed to a production backup set.")
    backup = metadata_payload.get("backup")
    if not isinstance(backup, dict) or backup.get("consistency") not in PRODUCTION_CONSISTENCY:
        raise RuntimeError("Production backup sets require a coordinated backup consistency mode.")
    if backup.get("filename") != postgres.name:
        raise RuntimeError("Restore metadata does not identify the PostgreSQL backup.")
    if int(backup.get("size_bytes", -1)) != postgres.stat().st_size:
        raise RuntimeError("Restore metadata size mismatch.")
    if backup.get("sha256") != sha256_file(postgres):
        raise RuntimeError("Restore metadata checksum mismatch.")
    return _artifact(root, metadata), metadata_payload


def _verification_record(root: Path, report_path: Path, postgres_record: dict[str, Any]) -> dict[str, Any]:
    payload = _read_json(report_path, 128 * 1024)
    if (
        int(payload.get("schema_version", -1)) != 1
        or payload.get("mode") != "preflight"
        or payload.get("status") != "passed"
        or payload.get("recoverable") is not True
    ):
        raise RuntimeError("Recovery verification report is not a successful full preflight.")
    source = payload.get("source_artifact")
    if not isinstance(source, dict):
        raise RuntimeError("Recovery report has no portable source-artifact binding.")
    for key in ("filename", "size_bytes", "sha256"):
        if source.get(key) != postgres_record.get(key):
            raise RuntimeError(f"Recovery report source binding mismatch: {key}")
    checks = payload.get("checks")
    passed = {
        str(check.get("name"))
        for check in checks if isinstance(check, dict) and check.get("status") == "passed"
    } if isinstance(checks, list) else set()
    missing = sorted(REQUIRED_RECOVERY_CHECKS - passed)
    if missing:
        raise RuntimeError(f"Recovery report is missing successful checks: {', '.join(missing)}")
    return _artifact(root, report_path)


def create_manifest(
    root: Path,
    output: Path,
    *,
    files: Path,
    postgres: Path | None = None,
    recovery: Path | None = None,
    verification: Path | None = None,
    reason: str = "scheduled",
) -> Path:
    root = root.expanduser().resolve()
    artifacts: dict[str, Any] = {"files": _artifact(root, files)}
    consistency = "files-only"
    if postgres:
        postgres_record = _artifact(root, postgres)
        metadata_record, metadata = _metadata_record(root, postgres)
        postgres_record["restore_metadata"] = metadata_record
        artifacts["postgres"] = postgres_record
        backup = metadata.get("backup")
        consistency = str(backup.get("consistency")) if isinstance(backup, dict) else "unrecorded"
        if not verification:
            raise RuntimeError("A PostgreSQL backup set requires a full recovery verification report.")
        artifacts["verification"] = _verification_record(root, verification, postgres_record)
    elif verification:
        raise RuntimeError("A recovery verification report without PostgreSQL is not supported.")
    if recovery:
        artifacts["recovery"] = _artifact(root, recovery)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason.strip() or "scheduled",
        "consistency": consistency,
        "committed": True,
        "artifacts": artifacts,
    }
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(output)
    output.chmod(0o600)
    return output


def validate_manifest(root: Path, manifest: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    manifest = manifest.expanduser().resolve()
    payload = _read_json(manifest, MAX_MANIFEST_BYTES)
    if int(payload.get("schema_version", -1)) != SCHEMA_VERSION or payload.get("committed") is not True:
        raise RuntimeError("Backup-set manifest is unsupported or not committed.")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict) or "files" not in artifacts:
        raise RuntimeError("Backup-set manifest has no files artifact.")
    if set(artifacts) - {"postgres", "files", "recovery", "verification"}:
        raise RuntimeError("Backup-set manifest contains an unsupported artifact type.")
    resolved: dict[str, Path] = {}
    for name, record in artifacts.items():
        if not isinstance(record, dict):
            raise RuntimeError(f"Invalid artifact record: {name}")
        relative = Path(str(record.get("path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"Unsafe backup-set artifact path: {relative}")
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RuntimeError("Backup-set artifact escaped infrastructure tree.") from exc
        _regular(path)
        if path.name != record.get("filename") or path.stat().st_size != int(record.get("size_bytes", -1)):
            raise RuntimeError(f"Backup-set artifact metadata mismatch: {name}")
        if not hmac.compare_digest(sha256_file(path), str(record.get("sha256") or "")):
            raise RuntimeError(f"Backup-set artifact checksum mismatch: {name}")
        _checksum(path)
        resolved[name] = path
    if "postgres" in artifacts:
        metadata_record = artifacts["postgres"].get("restore_metadata")
        if not isinstance(metadata_record, dict):
            raise RuntimeError("PostgreSQL artifact has no restore-metadata binding.")
        metadata_path = (root / str(metadata_record.get("path") or "")).resolve()
        expected_metadata_record, _metadata_payload = _metadata_record(root, resolved["postgres"])
        if metadata_record != expected_metadata_record:
            raise RuntimeError("Restore-metadata binding mismatch in backup set.")
        if metadata_path != (root / expected_metadata_record["path"]).resolve():
            raise RuntimeError("Restore-metadata path mismatch in backup set.")
        if "verification" not in resolved:
            raise RuntimeError("PostgreSQL backup set has no recovery verification report.")
        _verification_record(root, resolved["verification"], artifacts["postgres"])
        if payload.get("consistency") not in PRODUCTION_CONSISTENCY:
            raise RuntimeError("Backup set is not production-consistent.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--files", type=Path, required=True)
    create.add_argument("--postgres", type=Path)
    create.add_argument("--recovery", type=Path)
    create.add_argument("--verification", type=Path)
    create.add_argument("--reason", default="scheduled")
    validate = sub.add_parser("validate")
    validate.add_argument("--root", type=Path, required=True)
    validate.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.command == "create":
        print(
            create_manifest(
                args.root,
                args.output,
                files=args.files,
                postgres=args.postgres,
                recovery=args.recovery,
                verification=args.verification,
                reason=args.reason,
            )
        )
    else:
        print(json.dumps(validate_manifest(args.root, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
