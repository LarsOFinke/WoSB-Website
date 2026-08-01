#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA_VERSION = 2
SUPPORTED_SCHEMAS = frozenset({1, 2})
MAX_METADATA_BYTES = 32 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized = value.strip()
        if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
            normalized = normalized[1:-1]
        values[key.strip()] = normalized
    return values


def _fingerprint_key(value: str) -> str | None:
    try:
        decoded = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, ValueError):
        return None
    if len(decoded) != 32:
        return None
    return hashlib.sha256(decoded).hexdigest()


def environment_key_fingerprints(env_path: Path) -> list[str]:
    values = read_env_values(env_path)
    fingerprints: list[str] = []
    for key in (item.strip() for item in values.get("WEBHOOK_ENCRYPTION_KEYS", "").split(",")):
        if not key:
            continue
        fingerprint = _fingerprint_key(key)
        if fingerprint and fingerprint not in fingerprints:
            fingerprints.append(fingerprint)

    database_url = values.get("DATABASE_URL", "")
    if database_url:
        derived = base64.urlsafe_b64encode(
            hashlib.sha256(
                f"royal-blackwater-fleet:webhooks:v1:{database_url}".encode("utf-8")
            ).digest()
        ).decode("ascii")
        fingerprint = _fingerprint_key(derived)
        if fingerprint and fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
    return fingerprints


def database_identity(env_path: Path) -> dict[str, str]:
    values = read_env_values(env_path)
    database_url = values.get("DATABASE_URL", "")
    hostname = ""
    port = ""
    if database_url:
        parsed = urlsplit(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
        hostname = parsed.hostname or ""
        port = str(parsed.port or "")
    return {
        "database": values.get("POSTGRES_DB", ""),
        "user": values.get("POSTGRES_USER", ""),
        "hostname": hostname,
        "port": port,
    }


def _revisions(value: str) -> list[str]:
    result: list[str] = []
    for item in value.split(","):
        revision = item.strip()
        if revision and revision not in result:
            result.append(revision)
    return result


def create_metadata(
    backup: Path,
    env_file: Path,
    version_file: Path,
    alembic_head: str,
    *,
    postgres_version: str = "",
    git_commit: str = "",
    reason: str = "unspecified",
    backup_format: str = "postgresql-plain-sql+gzip",
    consistency: str = "uncoordinated",
) -> Path:
    if not backup.is_file():
        raise RuntimeError(f"Backup file does not exist: {backup}")
    if not env_file.is_file():
        raise RuntimeError(f"Environment file does not exist: {env_file}")
    fingerprints = environment_key_fingerprints(env_file)
    if not fingerprints:
        raise RuntimeError(
            "No valid restore encryption-key fingerprints could be derived from the environment."
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backup": {
            "filename": backup.name,
            "size_bytes": backup.stat().st_size,
            "sha256": sha256_file(backup),
            "reason": reason.strip() or "unspecified",
            "format": backup_format.strip() or "unknown",
            "consistency": consistency.strip() or "uncoordinated",
        },
        "application": {
            "version": version_file.read_text(encoding="utf-8").strip()
            if version_file.is_file()
            else "",
            "git_commit": git_commit.strip(),
            "alembic_revisions": _revisions(alembic_head),
        },
        "database": {
            **database_identity(env_file),
            "postgres_version": postgres_version.strip(),
        },
        "security": {
            "secret_key_fingerprints": fingerprints,
            "secret_key_count": len(fingerprints),
        },
    }
    target = Path(f"{backup}.restore.json")
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(target)
    target.chmod(0o600)
    checksum = Path(f"{target}.sha256")
    checksum.write_text(f"{sha256_file(target)}  {target.name}\n", encoding="ascii")
    checksum.chmod(0o600)
    return target


def validate_metadata(metadata_path: Path, backup: Path) -> dict[str, object]:
    if not metadata_path.is_file() or metadata_path.stat().st_size > MAX_METADATA_BYTES:
        raise RuntimeError("Restore metadata is missing or unexpectedly large.")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or int(payload.get("schema_version", -1)) not in SUPPORTED_SCHEMAS:
        raise RuntimeError("Unsupported restore-metadata schema.")
    backup_data = payload.get("backup")
    if not isinstance(backup_data, dict):
        raise RuntimeError("Restore metadata has no backup record.")
    if backup_data.get("filename") != backup.name:
        raise RuntimeError("Restore metadata filename does not match the backup.")
    if int(backup_data.get("size_bytes", -1)) != backup.stat().st_size:
        raise RuntimeError("Restore metadata size does not match the backup.")
    if backup_data.get("sha256") != sha256_file(backup):
        raise RuntimeError("Restore metadata checksum does not match the backup.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("backup", type=Path)
    create.add_argument("env_file", type=Path)
    create.add_argument("version_file", type=Path)
    create.add_argument("alembic_head")
    create.add_argument("--postgres-version", default="")
    create.add_argument("--git-commit", default="")
    create.add_argument("--reason", default="unspecified")
    create.add_argument("--format", dest="backup_format", default="postgresql-plain-sql+gzip")
    create.add_argument("--consistency", default="uncoordinated")

    fingerprints = subparsers.add_parser("fingerprints")
    fingerprints.add_argument("env_file", type=Path)

    validate = subparsers.add_parser("validate")
    validate.add_argument("metadata", type=Path)
    validate.add_argument("backup", type=Path)

    args = parser.parse_args()
    if args.command == "create":
        print(
            create_metadata(
                args.backup,
                args.env_file,
                args.version_file,
                args.alembic_head,
                postgres_version=args.postgres_version,
                git_commit=args.git_commit,
                reason=args.reason,
                backup_format=args.backup_format,
                consistency=args.consistency,
            )
        )
    elif args.command == "fingerprints":
        print(json.dumps(environment_key_fingerprints(args.env_file)))
    else:
        print(json.dumps(validate_metadata(args.metadata, args.backup), sort_keys=True))


if __name__ == "__main__":
    main()
