from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from contracts.recovery.contract import (  # noqa: E402
    MigrationGraph,
    assess_compatibility,
    descriptor_from_manifest,
    is_production_consistent,
)
from infrastructure.scripts.backup.backup_set_manifest import (  # type: ignore[import-not-found]  # noqa: E402
    create_manifest,
    validate_manifest,
)


def _migration(path: Path, revision: str, down: str | None) -> None:
    path.write_text(
        f"revision = {revision!r}\ndown_revision = {down!r}\n",
        encoding="utf-8",
    )


def _sidecar(path: Path) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    Path(f"{path}.sha256").write_text(f"{digest}  {path.name}\n", encoding="ascii")


def test_migration_contract_accepts_forward_upgrade_and_rejects_future(tmp_path: Path) -> None:
    versions = tmp_path / "versions"
    versions.mkdir()
    _migration(versions / "001.py", "001", None)
    _migration(versions / "002.py", "002", "001")
    graph = MigrationGraph.from_directory(versions)
    descriptor = descriptor_from_manifest(
        {
            "schema_version": 2,
            "backup": {"consistency": "application-quiesced"},
            "application": {"alembic_revisions": ["001"]},
        }
    )
    assessment = assess_compatibility(descriptor, graph)
    assert assessment.status == "upgrade"
    assert assessment.compatible is True
    assert assessment.migration_required is True
    assert is_production_consistent(descriptor) is True

    future = descriptor_from_manifest(
        {
            "schema_version": 2,
            "backup": {"consistency": "application-quiesced"},
            "application": {"alembic_revisions": ["999"]},
        }
    )
    assert assess_compatibility(future, graph).status == "unknown_revision"
    assert assess_compatibility(future, graph).compatible is False


def test_backup_set_requires_portable_successful_recovery_report(tmp_path: Path) -> None:
    root = tmp_path / "infra"
    postgres_dir = root / "data/backups/postgres"
    files_dir = root / "data/backups/files"
    reports_dir = root / "data/backups/reports"
    sets_dir = root / "data/backups/sets"
    for directory in (postgres_dir, files_dir, reports_dir, sets_dir):
        directory.mkdir(parents=True)
    postgres = postgres_dir / "rbf.sql.gz"
    postgres.write_bytes(b"postgres-dump")
    _sidecar(postgres)
    metadata = Path(f"{postgres}.restore.json")
    metadata.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "backup": {
                    "filename": postgres.name,
                    "size_bytes": postgres.stat().st_size,
                    "sha256": hashlib.sha256(postgres.read_bytes()).hexdigest(),
                    "consistency": "application-quiesced",
                },
                "application": {"alembic_revisions": ["001"]},
            }
        ),
        encoding="utf-8",
    )
    _sidecar(metadata)
    files = files_dir / "files.tar.gz"
    files.write_bytes(b"files")
    _sidecar(files)
    report = reports_dir / "report.json"
    checks = [
        "metadata_compatibility",
        "staging_database_creation",
        "postgres_import",
        "migration_and_schema_preflight",
        "secret_key_preflight",
        "application_readiness_preflight",
        "preflight_cleanup",
    ]
    report.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mode": "preflight",
                "status": "passed",
                "recoverable": True,
                "source_artifact": {
                    "filename": postgres.name,
                    "size_bytes": postgres.stat().st_size,
                    "sha256": hashlib.sha256(postgres.read_bytes()).hexdigest(),
                },
                "checks": [{"name": name, "status": "passed"} for name in checks],
            }
        ),
        encoding="utf-8",
    )
    _sidecar(report)
    target = sets_dir / "set.json"
    create_manifest(root, target, files=files, postgres=postgres, verification=report)
    _sidecar(target)
    assert validate_manifest(root, target)["committed"] is True

    report_payload = json.loads(report.read_text())
    report_payload["source_artifact"]["sha256"] = "0" * 64
    report.write_text(json.dumps(report_payload), encoding="utf-8")
    _sidecar(report)
    try:
        validate_manifest(root, target)
    except RuntimeError as exc:
        assert "source binding mismatch" in str(exc) or "checksum mismatch" in str(exc)
    else:
        raise AssertionError("Tampered recovery proof must be rejected")
