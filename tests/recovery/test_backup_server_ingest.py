from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_ingest():
    path = ROOT / "tools/backup-server/rbf-backup-ingest.py"
    spec = importlib.util.spec_from_file_location("rbf_backup_ingest_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_artifact(root: Path, name: str, content: bytes) -> dict[str, object]:
    path = root / name
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    (root / f"{name}.sha256").write_text(f"{digest}  {name}\n", encoding="ascii")
    return {"filename": name, "size_bytes": len(content), "sha256": digest}


def create_submission(
    incoming: Path,
    *,
    valid_report: bool = True,
    include_recovery: bool = True,
    extra_artifact: bool = False,
) -> tuple[Path, str]:
    files = write_artifact(incoming, "rbf-files-20260822T100000Z.tar.gz", b"files")
    postgres = write_artifact(incoming, "rbf-postgres-20260822T100000Z.dump", b"postgres")
    metadata = write_artifact(
        incoming,
        "rbf-postgres-20260822T100000Z.dump.restore.json",
        b'{"schema_version":2}',
    )
    postgres["restore_metadata"] = metadata
    checks = [
        "dump_inventory",
        "staging_database_restore",
        "flyway_validation",
        "application_readiness",
        "preflight_cleanup",
    ]
    report_payload = {
        "schema_version": 2,
        "mode": "preflight",
        "status": "passed" if valid_report else "failed",
        "recoverable": valid_report,
        "checks": [{"name": name, "status": "passed"} for name in checks],
    }
    verification = write_artifact(
        incoming,
        "rbf-postgres-preflight-20260822T100000Z-123.json",
        json.dumps(report_payload).encode(),
    )
    artifacts = {
        "files": files,
        "postgres": postgres,
        "verification": verification,
    }
    if include_recovery:
        artifacts["recovery"] = write_artifact(
            incoming, "rbf-recovery-20260822T100000Z.tar.gz.age", b"encrypted"
        )
    if extra_artifact:
        artifacts["unexpected"] = write_artifact(incoming, "unexpected.bin", b"unexpected")
    manifest = incoming / "rbf-backup-set-20260822T100000Z-123.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "committed": True,
                "consistency": "application-quiesced",
                "artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    (incoming / f"{manifest.name}.sha256").write_text(
        f"{digest}  {manifest.name}\n", encoding="ascii"
    )
    return manifest, digest


def test_backup_server_validates_and_copies_set_before_publishing_manifest(
    tmp_path, monkeypatch
) -> None:
    module = load_ingest()
    incoming = tmp_path / "incoming"
    committed = tmp_path / "data"
    receipts = tmp_path / "receipts"
    for path in (incoming, committed, receipts):
        path.mkdir()
    manifest, digest = create_submission(incoming)
    monkeypatch.setattr(module.os, "chown", lambda *_args: None)

    module.process_manifest(incoming, committed, receipts, manifest, 1000, 1001)

    receipt = json.loads(
        (receipts / f"{manifest.name}.receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "accepted"
    assert receipt["manifest_sha256"] == digest
    assert (committed / manifest.name).is_file()
    assert not any(incoming.iterdir())
    assert all(path.stat().st_mode & 0o777 == 0o640 for path in committed.iterdir())


def test_backup_server_rejects_unrecoverable_submission_without_committing(
    tmp_path, monkeypatch
) -> None:
    module = load_ingest()
    incoming = tmp_path / "incoming"
    committed = tmp_path / "data"
    receipts = tmp_path / "receipts"
    for path in (incoming, committed, receipts):
        path.mkdir()
    manifest, _digest = create_submission(incoming, valid_report=False)
    monkeypatch.setattr(module.os, "chown", lambda *_args: None)

    module.process_manifest(incoming, committed, receipts, manifest, 1000, 1001)

    receipt = json.loads(
        (receipts / f"{manifest.name}.receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "rejected"
    assert not any(committed.iterdir())


def test_backup_server_rejects_core_set_without_encrypted_recovery_bundle(
    tmp_path, monkeypatch
) -> None:
    module = load_ingest()
    incoming = tmp_path / "incoming"
    committed = tmp_path / "data"
    receipts = tmp_path / "receipts"
    for path in (incoming, committed, receipts):
        path.mkdir()
    manifest, _digest = create_submission(incoming, include_recovery=False)
    monkeypatch.setattr(module.os, "chown", lambda *_args: None)

    module.process_manifest(incoming, committed, receipts, manifest, 1000, 1001)

    receipt = json.loads(
        (receipts / f"{manifest.name}.receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "rejected"
    assert "recovery artifacts" in receipt["detail"]
    assert not any(committed.iterdir())


def test_backup_server_rejects_unknown_artifact_types(tmp_path, monkeypatch) -> None:
    module = load_ingest()
    incoming = tmp_path / "incoming"
    committed = tmp_path / "data"
    receipts = tmp_path / "receipts"
    for path in (incoming, committed, receipts):
        path.mkdir()
    manifest, _digest = create_submission(incoming, extra_artifact=True)
    monkeypatch.setattr(module.os, "chown", lambda *_args: None)

    module.process_manifest(incoming, committed, receipts, manifest, 1000, 1001)

    receipt = json.loads(
        (receipts / f"{manifest.name}.receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "rejected"
    assert not any(committed.iterdir())


def test_provisioner_keeps_controller_storage_local_and_private() -> None:
    provisioner = (ROOT / "tools/backup-server/provision-rbf-backup-server.sh").read_text()
    assert 'install -d -m 0700 -o root -g root "$STORAGE"' in provisioner
    assert 'destination_directory": sys.argv[6]' in provisioner
    assert 'ReadWritePaths=${STORAGE}' in provisioner
    assert '/run/rbf-recovery-${ENVIRONMENT}/controller.lock' in provisioner
    assert 'RuntimeDirectory=rbf-recovery-${ENVIRONMENT}' in provisioner
    assert 'requested_storage_directory' in provisioner


def test_provisioner_isolates_test_and_production_resources() -> None:
    provisioner = (ROOT / "tools/backup-server/provision-rbf-backup-server.sh").read_text()
    assert 'username != f"rbf-backup-controller-{environment}"' in provisioner
    assert 'storage != f"/backups/wosb/{environment}"' in provisioner
    assert 'TARGET_ROOT="$STATE_ROOT/$ENVIRONMENT"' in provisioner
    assert 'Automatic published-export sync is enabled every minute' in provisioner
    assert 'must be run as root' in provisioner
    assert 'systemctl disable --now' in provisioner
    assert 'destination_directory": sys.argv[6]' in provisioner


def test_provisioner_uses_outbound_pinned_controller_connections() -> None:
    provisioner = (ROOT / "tools/backup-server/provision-rbf-backup-server.sh").read_text()
    assert 'WEBSITE_HOST_KEY' in provisioner
    assert 'ACTUAL_FINGERPRINT="$(ssh-keygen -lf' in provisioner
    assert '/usr/local/bin/rbf-recovery-tool run --target ${ENVIRONMENT}' in provisioner
    assert 'transport": "recovery-controller-pull-v1"' in provisioner
    assert 'curl ' not in provisioner
    assert 'github.com' not in provisioner.lower()
