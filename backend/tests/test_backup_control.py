from __future__ import annotations

import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.accounts.services.auth_service import create_user
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _reset_control() -> tuple[Path, Path]:
    request_dir = Path(settings.control_request_dir)
    status_dir = Path(settings.control_status_dir)
    for path in {request_dir, status_dir}:
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
    return request_dir, status_dir


def test_backup_control_is_admin_only_and_never_returns_private_keys() -> None:
    request_dir, status_dir = _reset_control()
    private_key = """-----BEGIN OPENSSH PRIVATE KEY-----
ZmFrZS10ZXN0LWtleQ==
-----END OPENSSH PRIVATE KEY-----
"""
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="backup-moderator",
                password="BlackwaterBackupMod123!",
                display_name="Backup Moderator",
                role=ROLE_MODERATOR,
            )
            create_user(
                db,
                username="backup-admin",
                password="BlackwaterBackupAdmin123!",
                display_name="Backup Admin",
                role=ROLE_ADMIN,
            )

        assert client.get("/api/admin/backups/status").status_code == 401
        _login(client, "backup-moderator", "BlackwaterBackupMod123!")
        assert client.get("/api/admin/backups/status").status_code == 403
        assert client.post("/api/admin/backups/run").status_code == 403
        assert client.post("/api/auth/logout").status_code == 204

        _login(client, "backup-admin", "BlackwaterBackupAdmin123!")
        initial = client.get("/api/admin/backups/status")
        assert initial.status_code == 200, initial.text
        assert initial.json()["connection"]["configured"] is False

        discovery = client.post(
            "/api/admin/backups/discover",
            json={"host": "backup.example.net", "port": 2222},
        )
        assert discovery.status_code == 202, discovery.text
        request_file = request_dir / "backup.request"
        request_payload = json.loads(request_file.read_text(encoding="utf-8"))
        assert request_payload["operation"] == "discover"
        assert request_payload["host"] == "backup.example.net"
        assert discovery.json()["status"]["state"] == "queued"

        request_file.unlink()
        configuration = client.put(
            "/api/admin/backups/configuration",
            json={
                "host": "backup.example.net",
                "port": 2222,
                "username": "rbf_backup",
                "remote_directory": "/srv/backups/rbf",
                "private_key": private_key,
                "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeHostKeyMaterialForTests=",
            },
        )
        assert configuration.status_code == 202, configuration.text
        response_text = configuration.text
        assert "OPENSSH PRIVATE KEY" not in response_text
        request_payload = json.loads(request_file.read_text(encoding="utf-8"))
        assert request_payload["private_key"] == private_key
        assert request_file.stat().st_mode & 0o077 == 0

        request_file.unlink()
        status_file = status_dir / "backup-status.json"
        status_file.write_text(
            json.dumps(
                {
                    "state": "succeeded",
                    "operation": "configure",
                    "message": "configured",
                    "connection": {
                        "configured": True,
                        "host": "backup.example.net",
                        "port": 2222,
                        "username": "rbf_backup",
                        "remote_directory": "/srv/backups/rbf",
                        "host_key_fingerprint": "SHA256:test",
                        "private_key_configured": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        status_response = client.get("/api/admin/backups/status")
        assert status_response.status_code == 200, status_response.text
        status_payload = status_response.json()
        assert status_payload["connection"]["configured"] is True
        assert private_key.strip() not in json.dumps(status_payload)
        assert "private_key" not in status_payload["connection"]

        queued_backup = client.post("/api/admin/backups/run")
        assert queued_backup.status_code == 202, queued_backup.text
        assert json.loads(request_file.read_text(encoding="utf-8"))["operation"] == "backup"

    _reset_control()


def test_backup_configuration_validation_rejects_shell_paths_and_urls() -> None:
    _reset_control()
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="backup-validation-admin",
                password="BlackwaterBackupValidation123!",
                display_name="Backup Validation Admin",
                role=ROLE_ADMIN,
            )
        _login(client, "backup-validation-admin", "BlackwaterBackupValidation123!")
        response = client.put(
            "/api/admin/backups/configuration",
            json={
                "host": "https://backup.example.net",
                "port": 22,
                "username": "rbf;rm",
                "remote_directory": "/srv/backups/../root",
                "private_key": "not-a-key",
                "host_key": "invalid",
            },
        )
        assert response.status_code == 422
    _reset_control()


def test_backup_requests_are_published_atomically_under_concurrency() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from app.modules.accounts.models.user import User
    from app.modules.admin.services.backup_control_service import (
        BackupControlError,
        request_backup_operation,
    )

    request_dir, _ = _reset_control()
    barrier = Barrier(2)
    user = User(username="backup-race-admin")

    def submit() -> str:
        barrier.wait()
        try:
            request_backup_operation(user, "backup")
        except BackupControlError:
            return "rejected"
        return "accepted"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(lambda _: submit(), range(2)))

    assert results == ["accepted", "rejected"]
    request_payload = json.loads((request_dir / "backup.request").read_text(encoding="utf-8"))
    assert request_payload["operation"] == "backup"
    assert request_payload["requested_by"] == "backup-race-admin"
    assert not list(request_dir.glob(".backup.request.*.tmp"))
    _reset_control()


def test_backup_status_reports_complete_recovery_artifacts() -> None:
    _, status_dir = _reset_control()
    (status_dir / "backup-status.json").write_text(
        json.dumps(
            {
                "state": "succeeded",
                "operation": "backup",
                "message": "verified",
                "artifacts": [
                    {
                        "artifact_type": "postgresql",
                        "filename": "rbf.sql.gz",
                        "size_bytes": 123,
                        "sha256": "a" * 64,
                        "remote_path": "/srv/backups/rbf.sql.gz",
                    },
                    {
                        "artifact_type": "files",
                        "filename": "rbf-files.tar.gz",
                        "size_bytes": 456,
                        "sha256": "b" * 64,
                        "remote_path": "/srv/backups/rbf-files.tar.gz",
                    },
                    {
                        "artifact_type": "recovery",
                        "filename": "rbf-recovery.tar.gz.age",
                        "size_bytes": 789,
                        "sha256": "c" * 64,
                        "remote_path": "/srv/backups/rbf-recovery.tar.gz.age",
                    },
                ],
                "connection": {"configured": False},
            }
        ),
        encoding="utf-8",
    )
    from app.modules.admin.services.backup_control_service import get_backup_control_status

    status = get_backup_control_status()
    assert [artifact.artifact_type for artifact in status.artifacts] == [
        "postgresql",
        "files",
        "recovery",
    ]
    assert status.artifacts[2].size_bytes == 789
    _reset_control()


def test_admin_backup_runner_creates_complete_recovery_artifacts(tmp_path, monkeypatch) -> None:
    import importlib.util

    runner_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_admin_runner", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")
    runner = module.Runner(tmp_path, request_file)
    runner.prepare()
    monkeypatch.setattr(runner, "load_connection", lambda: {"remote_directory": "/remote"})
    monkeypatch.setattr(runner, "recovery_enabled", lambda: True)
    transfers = []

    def fake_run(command, **kwargs):
        class Result:
            returncode = 0
            stdout = "coordinated backup complete\n"
            stderr = ""

        arguments = list(command)
        for flag, label in (
            ("--postgres-result", "postgresql"),
            ("--files-result", "files"),
            ("--recovery-result", "recovery"),
            ("--verification-result", "verification"),
            ("--backup-set-result", "backup_set"),
        ):
            result_path = Path(arguments[arguments.index(flag) + 1])
            artifact = tmp_path / f"{label}.archive"
            artifact.write_bytes(label.encode())
            Path(f"{artifact}.sha256").write_text("checksum", encoding="utf-8")
            result_path.write_text(str(artifact), encoding="utf-8")
        return Result()

    def fake_transfer(_config, artifact, artifact_type):
        transfers.append(artifact_type)
        return {
            "artifact_type": artifact_type,
            "filename": artifact.name,
            "size_bytes": artifact.stat().st_size,
            "sha256": "c" * 64,
            "remote_path": f"/remote/{artifact.name}",
        }

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "transfer", fake_transfer)
    result = runner.create_and_transfer_backup()

    assert transfers == ["postgresql", "files", "recovery", "verification", "backup_set"]
    assert [row["artifact_type"] for row in result["artifacts"]] == [
        "postgresql",
        "files",
        "recovery",
    ]
    data_script = (
        Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-data.sh"
    ).read_text(encoding="utf-8")
    assert "backup_paths=(uploads)" in data_script
    assert "for optional_path in certs letsencrypt uptime-kuma" in data_script
    assert "BACKUP_RESULT_FILE" in data_script


def test_local_backup_restore_requires_bootstrap_admin_and_hides_approval_token() -> None:
    import hashlib
    request_dir, _ = _reset_control()
    backup_id = "d" * 64
    approval_token = "A" * 32
    with TestClient(app) as client:
        with SessionLocal() as db:
            regular_admin = create_user(
                db,
                username="backup-regular-admin",
                password="BlackwaterRegularAdmin123!",
                display_name="Regular Backup Admin",
                role=ROLE_ADMIN,
            )
            bootstrap_admin = create_user(
                db,
                username="backup-bootstrap-admin",
                password="BlackwaterBootstrapAdmin123!",
                display_name="Bootstrap Backup Admin",
                role=ROLE_ADMIN,
            )
            regular_admin.is_bootstrap_admin = False
            bootstrap_admin.is_bootstrap_admin = True
            db.commit()

        _login(client, "backup-regular-admin", "BlackwaterRegularAdmin123!")
        scan = client.post("/api/admin/backups/local/scan")
        assert scan.status_code == 202, scan.text
        (request_dir / "backup.request").unlink()
        denied = client.post(
            "/api/admin/backups/local/restore",
            json={
                "backup_id": backup_id,
                "approval_token": approval_token,
                "confirmation": "RESTORE DATABASE",
            },
        )
        assert denied.status_code == 403
        assert client.post("/api/auth/logout").status_code == 204

        _login(client, "backup-bootstrap-admin", "BlackwaterBootstrapAdmin123!")
        invalid_confirmation = client.post(
            "/api/admin/backups/local/restore",
            json={
                "backup_id": backup_id,
                "approval_token": approval_token,
                "confirmation": "restore database",
            },
        )
        assert invalid_confirmation.status_code == 422

        accepted = client.post(
            "/api/admin/backups/local/restore",
            json={
                "backup_id": backup_id,
                "approval_token": approval_token,
                "confirmation": "RESTORE DATABASE",
            },
        )
        assert accepted.status_code == 202, accepted.text
        assert approval_token not in accepted.text
        request_payload = json.loads((request_dir / "backup.request").read_text(encoding="utf-8"))
        assert request_payload == {
            "requested_by": "backup-bootstrap-admin",
            "requested_at": request_payload["requested_at"],
            "operation": "restore_postgresql",
            "backup_id": backup_id,
            "approval_token_sha256": hashlib.sha256(approval_token.encode("utf-8")).hexdigest(),
        }
        assert (request_dir / "backup.request").stat().st_mode & 0o077 == 0
    _reset_control()


def test_local_backup_catalog_accepts_only_verified_regular_files(tmp_path) -> None:
    import hashlib
    import importlib.util

    module_path = (
        Path(__file__).parents[2] / "infrastructure/scripts/backup/local_backup_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("local_backup_catalog_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    backup_dir = infra / "data/backups/postgres"
    backup_dir.mkdir(parents=True)
    valid = backup_dir / "rbf-20260731T100000Z.sql.gz"
    valid.write_bytes(b"verified-backup")
    digest = hashlib.sha256(valid.read_bytes()).hexdigest()
    Path(f"{valid}.sha256").write_text(f"{digest}  {valid.name}\n", encoding="ascii")

    invalid = backup_dir / "rbf-20260731T100001Z.sql.gz"
    invalid.write_bytes(b"tampered")
    Path(f"{invalid}.sha256").write_text(f"{'0' * 64}  {invalid.name}\n", encoding="ascii")

    records, skipped = module.scan_local_postgres_backups(infra)
    assert len(records) == 1
    assert skipped == 1
    record = records[0]
    assert record.filename == valid.name
    assert record.sha256 == digest
    assert len(record.backup_id) == 64
    assert module.resolve_local_postgres_backup(infra, record.backup_id).path == valid
    try:
        module.resolve_local_postgres_backup(infra, "f" * 64)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Unknown opaque backup ids must be rejected")


def test_database_restore_approval_is_short_lived_and_one_time(tmp_path) -> None:
    from datetime import datetime, timedelta, timezone
    import hashlib
    import importlib.util

    module_path = (
        Path(__file__).parents[2] / "infrastructure/scripts/backup/local_backup_catalog.py"
    )
    spec = importlib.util.spec_from_file_location("local_backup_approval_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    approval = infra / "data/control/secrets/database-restore-approval.json"
    approval.parent.mkdir(parents=True)
    token = "safe_restore_token_1234567890"
    approval.write_text(
        json.dumps(
            {
                "purpose": "database_restore",
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    approval.chmod(0o600)
    module.consume_database_restore_approval(infra, hashlib.sha256(token.encode()).hexdigest())
    assert not approval.exists()
    try:
        module.consume_database_restore_approval(infra, hashlib.sha256(token.encode()).hexdigest())
    except RuntimeError:
        pass
    else:
        raise AssertionError("Restore approval tokens must not be reusable")

    approval.write_text(
        json.dumps(
            {
                "purpose": "database_restore",
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    approval.chmod(0o600)
    try:
        module.consume_database_restore_approval(infra, hashlib.sha256(b"wrong-token").hexdigest())
    except RuntimeError:
        pass
    else:
        raise AssertionError("Incorrect restore approvals must be rejected")
    assert not approval.exists(), "A failed approval attempt must consume the one-time token"


def test_admin_runner_restore_uses_verified_catalog_and_hashed_one_time_approval(
    tmp_path, monkeypatch
) -> None:
    from datetime import datetime, timedelta, timezone
    import hashlib
    import importlib.util

    runner_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_admin_restore_runner", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    backup_dir = infra / "data/backups/postgres"
    backup_dir.mkdir(parents=True)
    backup = backup_dir / "rbf-20260731T130000Z.sql.gz"
    backup.write_bytes(b"valid-gzip-placeholder")
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    Path(f"{backup}.sha256").write_text(f"{digest}  {backup.name}\n", encoding="ascii")
    metadata = Path(f"{backup}.restore.json")
    metadata.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "backup": {
                    "filename": backup.name,
                    "size_bytes": backup.stat().st_size,
                    "sha256": digest,
                    "consistency": "application-quiesced",
                },
                "application": {"alembic_revisions": ["0020_raid_helper_premium"]},
                "security": {"secret_key_fingerprints": []},
            }
        ),
        encoding="utf-8",
    )
    metadata_digest = hashlib.sha256(metadata.read_bytes()).hexdigest()
    Path(f"{metadata}.sha256").write_text(
        f"{metadata_digest}  {metadata.name}\n", encoding="ascii"
    )
    files = infra / "data/backups/files/rbf-files.tar.gz"
    files.parent.mkdir(parents=True)
    files.write_bytes(b"files")
    files_digest = hashlib.sha256(files.read_bytes()).hexdigest()
    Path(f"{files}.sha256").write_text(f"{files_digest}  {files.name}\n", encoding="ascii")
    report = infra / "data/backups/reports/preflight.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mode": "preflight",
                "status": "passed",
                "recoverable": True,
                "source_artifact": {
                    "filename": backup.name,
                    "size_bytes": backup.stat().st_size,
                    "sha256": digest,
                },
                "checks": [
                    {"name": name, "status": "passed"}
                    for name in (
                        "metadata_compatibility",
                        "staging_database_creation",
                        "postgres_import",
                        "migration_and_schema_preflight",
                        "secret_key_preflight",
                        "application_readiness_preflight",
                        "preflight_cleanup",
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    report_digest = hashlib.sha256(report.read_bytes()).hexdigest()
    Path(f"{report}.sha256").write_text(f"{report_digest}  {report.name}\n", encoding="ascii")
    import backup_set_manifest
    backup_set = infra / "data/backups/sets/rbf-backup-set-test.json"
    backup_set_manifest.create_manifest(
        infra,
        backup_set,
        files=files,
        postgres=backup,
        verification=report,
    )
    set_digest = hashlib.sha256(backup_set.read_bytes()).hexdigest()
    Path(f"{backup_set}.sha256").write_text(
        f"{set_digest}  {backup_set.name}\n", encoding="ascii"
    )

    records, _ = module.scan_local_postgres_backups(infra)
    assert len(records) == 1
    token = "host_restore_approval_token_123456"
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    approval = infra / "data/control/secrets/database-restore-approval.json"
    approval.parent.mkdir(parents=True)
    approval.write_text(
        json.dumps(
            {
                "purpose": "database_restore",
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                "token_sha256": token_hash,
            }
        ),
        encoding="utf-8",
    )
    approval.chmod(0o600)

    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request_file)
    runner.prepare()
    runner.request = {
        "backup_id": records[0].backup_id,
        "approval_token_sha256": token_hash,
    }
    calls = []

    class Result:
        returncode = 0
        stdout = "restore complete\n"
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    result = runner.restore_postgresql()

    assert not approval.exists()
    assert "approval_token_sha256" not in runner.request
    assert result["local_database_backups"][0]["backup_id"] == records[0].backup_id
    assert calls[0][0] == ["gzip", "-t", str(backup)]
    assert calls[1][0][-1] == str(backup)
    assert calls[1][1]["env"]["RBF_RESTORE_LOCK_HELD"] == "true"


def test_admin_restore_consumes_host_approval_before_backup_selection(tmp_path) -> None:
    from datetime import datetime, timedelta, timezone
    import hashlib
    import importlib.util

    runner_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_admin_approval_order", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    approval = infra / "data/control/secrets/database-restore-approval.json"
    approval.parent.mkdir(parents=True)
    token = "host_restore_approval_order_123456"
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    approval.write_text(
        json.dumps(
            {
                "purpose": "database_restore",
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                "token_sha256": token_hash,
            }
        ),
        encoding="utf-8",
    )
    approval.chmod(0o600)

    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request_file)
    runner.prepare()
    runner.request = {
        "backup_id": "f" * 64,
        "approval_token_sha256": token_hash,
    }

    try:
        runner.restore_postgresql()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Unknown backup selections must be rejected")
    assert not approval.exists(), "Host approval must be consumed before backup selection"
    assert "approval_token_sha256" not in runner.request


def test_postgres_backup_metadata_reports_encryption_key_compatibility(tmp_path) -> None:
    import importlib.util
    import hashlib
    from cryptography.fernet import Fernet

    scripts = Path(__file__).parents[2] / "infrastructure/scripts/backup"
    metadata_spec = importlib.util.spec_from_file_location(
        "backup_metadata_compatibility_test", scripts / "backup_metadata.py"
    )
    assert metadata_spec and metadata_spec.loader
    metadata = importlib.util.module_from_spec(metadata_spec)
    metadata_spec.loader.exec_module(metadata)

    catalog_spec = importlib.util.spec_from_file_location(
        "local_backup_catalog_compatibility_test", scripts / "local_backup_catalog.py"
    )
    assert catalog_spec and catalog_spec.loader
    catalog = importlib.util.module_from_spec(catalog_spec)
    import sys
    sys.modules[catalog_spec.name] = catalog
    catalog_spec.loader.exec_module(catalog)

    infra = tmp_path / "infrastructure"
    backup_dir = infra / "data/backups/postgres"
    backup_dir.mkdir(parents=True)
    backup = backup_dir / "rbf-20260731T140000Z.sql.gz"
    backup.write_bytes(b"database-backup")
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    Path(f"{backup}.sha256").write_text(f"{digest}  {backup.name}\n", encoding="ascii")
    key = Fernet.generate_key().decode("ascii")
    env = infra / ".env"
    env.write_text(
        "POSTGRES_USER=rbf\nPOSTGRES_DB=rbf\nPOSTGRES_PASSWORD=test\n"
        "DATABASE_URL=postgresql+psycopg://rbf:test@postgres:5432/rbf\n"
        f"WEBHOOK_ENCRYPTION_KEYS={key}\n",
        encoding="utf-8",
    )
    version = tmp_path / "VERSION"
    version.write_text("1.0.0\n", encoding="utf-8")
    metadata.create_metadata(backup, env, version, "0020_raid_helper_premium")

    records, skipped = catalog.scan_local_postgres_backups(infra)
    assert skipped == 0
    assert len(records) == 1
    assert records[0].restore_metadata_verified is True
    assert records[0].encryption_keys_compatible is True
    assert records[0].alembic_head == "0020_raid_helper_premium"

    env.write_text(
        "POSTGRES_USER=rbf\nPOSTGRES_DB=rbf\nPOSTGRES_PASSWORD=other\n"
        "DATABASE_URL=postgresql+psycopg://rbf:other@postgres:5432/rbf\n"
        f"WEBHOOK_ENCRYPTION_KEYS={Fernet.generate_key().decode('ascii')}\n",
        encoding="utf-8",
    )
    records, skipped = catalog.scan_local_postgres_backups(infra)
    assert skipped == 0
    assert records[0].encryption_keys_compatible is False


def test_restore_script_uses_staging_preflight_and_automatic_rollback() -> None:
    script = (
        Path(__file__).parents[2]
        / "infrastructure/scripts/backup/restore-postgres.sh"
    ).read_text(encoding="utf-8")
    assert "CREATE DATABASE %I OWNER %I TEMPLATE template0" in script
    assert "python -m app.db.restore_preflight" in script
    assert "ALTER DATABASE %I RENAME TO %I" in script
    assert "rollback_database_swap" in script
    assert "-c \"SELECT pg_terminate_backend" not in script


def test_backup_enrollment_endpoints_publish_only_public_material() -> None:
    request_dir, status_dir = _reset_control()
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="backup-enrollment-admin",
                password="BlackwaterEnrollmentAdmin123!",
                display_name="Backup Enrollment Admin",
                role=ROLE_ADMIN,
            )
        _login(client, "backup-enrollment-admin", "BlackwaterEnrollmentAdmin123!")
        key_prepared = client.post("/api/admin/backups/key/prepare")
        assert key_prepared.status_code == 202, key_prepared.text
        request_payload = json.loads((request_dir / "backup.request").read_text(encoding="utf-8"))
        assert request_payload["operation"] == "prepare_key"
        assert "private_key" not in json.dumps(request_payload)

        (request_dir / "backup.request").unlink()
        prepared = client.post("/api/admin/backups/enrollment/prepare")
        assert prepared.status_code == 202, prepared.text
        request_payload = json.loads((request_dir / "backup.request").read_text(encoding="utf-8"))
        assert request_payload["operation"] == "prepare_enrollment"
        assert "private_key" not in json.dumps(request_payload)

        (request_dir / "backup.request").unlink()
        (status_dir / "backup-status.json").write_text(
            json.dumps(
                {
                    "state": "succeeded",
                    "operation": "prepare_enrollment",
                    "message": "prepared",
                    "enrollment_request": {"enrollment_id": "A" * 32},
                    "connection": {"configured": False},
                }
            ),
            encoding="utf-8",
        )
        response_json = json.dumps(
            {
                "schema_version": 1,
                "kind": "rbf-backup-enrollment-response",
                "enrollment_id": "A" * 32,
                "created_at": "2026-08-01T10:00:00+00:00",
                "host": "backup.example.net",
                "port": 22,
                "username": "rbf-backup",
                "remote_directory": "/data",
                "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
                "host_key_fingerprint": "SHA256:" + "A" * 43,
                "age_recipient": "age1" + "a" * 58,
                "managed_server": True,
            }
        )
        applied = client.post(
            "/api/admin/backups/enrollment/apply",
            json={"response_json": response_json},
        )
        assert applied.status_code == 202, applied.text
        request_payload = json.loads((request_dir / "backup.request").read_text(encoding="utf-8"))
        assert request_payload["operation"] == "apply_enrollment"
        assert json.loads(request_payload["response_json"]) == json.loads(response_json)
        assert "PRIVATE KEY" not in applied.text
    _reset_control()


def test_backup_enrollment_apply_validates_file_before_queueing() -> None:
    request_dir, status_dir = _reset_control()
    with TestClient(app) as client:
        with SessionLocal() as db:
            create_user(
                db,
                username="backup-enrollment-validation-admin",
                password="BlackwaterEnrollmentValidation123!",
                display_name="Backup Enrollment Validation Admin",
                role=ROLE_ADMIN,
            )
        _login(client, "backup-enrollment-validation-admin", "BlackwaterEnrollmentValidation123!")
        (status_dir / "backup-status.json").write_text(
            json.dumps(
                {
                    "state": "succeeded",
                    "operation": "prepare_enrollment",
                    "enrollment_request": {"enrollment_id": "A" * 32},
                    "connection": {"configured": False},
                }
            ),
            encoding="utf-8",
        )
        invalid = client.post(
            "/api/admin/backups/enrollment/apply",
            json={"response_json": json.dumps({"kind": "rbf-backup-server-provisioning-result"})},
        )
        assert invalid.status_code == 422
        assert not (request_dir / "backup.request").exists()

        incomplete = client.post(
            "/api/admin/backups/enrollment/apply",
            json={
                "response_json": json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "rbf-backup-enrollment-response",
                        "enrollment_id": "A" * 32,
                        "managed_server": True,
                    }
                )
            },
        )
        assert incomplete.status_code == 422
        assert not (request_dir / "backup.request").exists()

        response = {
            "schema_version": 1,
            "kind": "rbf-backup-enrollment-response",
            "enrollment_id": "A" * 32,
            "created_at": "2026-08-01T10:00:00+00:00",
            "host": "backup.example.net",
            "port": 22,
            "username": "rbf-backup",
            "remote_directory": "/data",
            "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
            "host_key_fingerprint": "SHA256:" + "A" * 43,
            "age_recipient": "age1" + "a" * 58,
            "managed_server": True,
        }
        accepted = client.post(
            "/api/admin/backups/enrollment/apply",
            json={"response_json": "\ufeff" + json.dumps(response)},
        )
        assert accepted.status_code == 202, accepted.text
        queued = json.loads((request_dir / "backup.request").read_text(encoding="utf-8"))
        assert json.loads(queued["response_json"])["enrollment_id"] == "A" * 32

    _reset_control()


def test_admin_backup_runner_prepares_and_applies_managed_enrollment(tmp_path, monkeypatch) -> None:
    import importlib.util

    runner_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_admin_runner_enrollment", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    (infra / ".env").parent.mkdir(parents=True, exist_ok=True)
    (infra / ".env").write_text(
        "BACKUP_RECOVERY_ENABLED=false\nBACKUP_AGE_RECIPIENT=\n",
        encoding="utf-8",
    )
    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request_file)
    runner.prepare()

    class Result:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(command, **_kwargs):
        command = [str(part) for part in command]
        if "-f" in command and "-t" in command:
            target = Path(command[command.index("-f") + 1])
            target.write_text("PRIVATE", encoding="utf-8")
            target.with_suffix(".pub").write_text("PUBLIC", encoding="utf-8")
            return Result()
        if "-y" in command:
            return Result(stdout="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIProductKey=\n")
        if "-lf" in command:
            return Result(stdout="256 SHA256:ProductUploadFingerprint test (ED25519)\n")
        raise AssertionError(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.socket, "gethostname", lambda: "wosb-prod")
    prepared = runner.prepare_enrollment()
    enrollment_id = prepared["enrollment_id"]
    assert runner.key_file.is_file()
    assert "PRIVATE" not in json.dumps(prepared)

    response = {
        "schema_version": 1,
        "kind": "rbf-backup-enrollment-response",
        "enrollment_id": enrollment_id,
        "host": "backup.example.net",
        "port": 22,
        "username": "rbf-backup",
        "remote_directory": "/data",
        "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
        "host_key_fingerprint": "SHA256:" + "B" * 43,
        "age_recipient": "age1" + "a" * 58,
        "managed_server": True,
    }
    runner.request = {"response_json": json.dumps(response)}
    monkeypatch.setattr(runner, "_scan_host_key", lambda *_args: None)
    monkeypatch.setattr(runner, "fingerprint_for_line", lambda _line: response["host_key_fingerprint"])
    monkeypatch.setattr(runner, "test_connection", lambda _config=None: None)
    applied = runner.apply_enrollment()
    assert applied["enrollment_applied"] is True
    config = json.loads(runner.config_file.read_text(encoding="utf-8"))
    assert config["managed_server"] is True
    assert config["remote_directory"] == "/data"
    env = (infra / ".env").read_text(encoding="utf-8")
    assert "BACKUP_RECOVERY_ENABLED=true" in env
    assert response["age_recipient"] in env
    assert not runner.enrollment_request_file.exists()
