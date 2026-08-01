#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load_runner(repository_root: Path):
    path = repository_root / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("rbf_backup_admin_runner_sync", path)
    if not spec or not spec.loader:
        raise RuntimeError("Could not load the protected backup transfer runner.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Runner


def _load_manifest_validator(infra: Path):
    path = infra / "scripts/backup/backup_set_manifest.py"
    spec = importlib.util.spec_from_file_location("rbf_backup_set_manifest_sync", path)
    if not spec or not spec.loader:
        raise RuntimeError("Could not load the backup-set validator.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_manifest


def _require_manifest_members(infra: Path, payload: dict, supplied: dict[str, Path]) -> None:
    records = payload.get("artifacts")
    if not isinstance(records, dict):
        raise RuntimeError("Backup-set manifest contains no artifacts.")
    for name, path in supplied.items():
        record = records.get(name)
        if name == "recovery" and path is None:
            if record is not None:
                raise RuntimeError("Recovery artifact exists in the set but was not supplied for transfer.")
            continue
        if path is None or not isinstance(record, dict):
            raise RuntimeError(f"Backup-set artifact is missing: {name}")
        expected = (infra / str(record.get("path") or "")).resolve()
        if expected != path.resolve():
            raise RuntimeError(f"Backup-set artifact argument does not match the committed manifest: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--infra", type=Path, required=True)
    parser.add_argument("--postgres", type=Path, required=True)
    parser.add_argument("--files", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--set", dest="backup_set", type=Path, required=True)
    parser.add_argument("--recovery", type=Path)
    args = parser.parse_args()

    infra = args.infra.resolve()
    validate_manifest = _load_manifest_validator(infra)
    manifest_payload = validate_manifest(infra, args.backup_set.resolve())
    _require_manifest_members(
        infra,
        manifest_payload,
        {
            "postgres": args.postgres.resolve(),
            "files": args.files.resolve(),
            "verification": args.verification.resolve(),
            "recovery": args.recovery.resolve() if args.recovery else None,
        },
    )
    Runner = _load_runner(infra.parent)
    runner = Runner(infra, infra / "data/control/run/scheduled-sync.request")
    runner.prepare()
    if not (runner.config_file.is_file() and runner.key_file.is_file() and runner.known_hosts_file.is_file()):
        print("Remote backup destination is not configured; committed local backup set retained.")
        return 0
    config = runner.load_connection()
    runner.test_connection(config)
    artifacts = [
        runner.transfer(config, args.postgres.resolve(), "postgresql"),
        runner.transfer(config, args.files.resolve(), "files"),
    ]
    if args.recovery and args.recovery.is_file():
        artifacts.append(runner.transfer(config, args.recovery.resolve(), "recovery"))
    runner.transfer(config, args.verification.resolve(), "verification")
    # The set manifest is deliberately published last as the remote commit marker.
    runner.transfer(config, args.backup_set.resolve(), "backup_set")
    print(json.dumps({"transferred": artifacts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
