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


def test_backup_status_reports_database_and_file_artifacts() -> None:
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
                ],
                "connection": {"configured": False},
            }
        ),
        encoding="utf-8",
    )
    from app.modules.admin.services.backup_control_service import get_backup_control_status

    status = get_backup_control_status()
    assert [artifact.artifact_type for artifact in status.artifacts] == ["postgresql", "files"]
    assert status.artifacts[1].size_bytes == 456
    _reset_control()


def test_admin_backup_runner_creates_database_and_file_artifacts(tmp_path, monkeypatch) -> None:
    import importlib.util

    runner_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_admin_runner", runner_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")
    runner = module.Runner(tmp_path, request_file)
    monkeypatch.setattr(runner, "load_connection", lambda: {"remote_directory": "/remote"})
    monkeypatch.setattr(runner, "test_connection", lambda _config: None)
    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        return {
            "artifact_type": kwargs["artifact_type"],
            "filename": f"{kwargs['artifact_type']}.archive",
            "size_bytes": 1,
            "sha256": "c" * 64,
            "remote_path": f"/remote/{kwargs['artifact_type']}.archive",
        }

    monkeypatch.setattr(runner, "create_backup_artifact", fake_create)
    result = runner.create_and_transfer_backup()

    assert [call["script_name"] for call in calls] == ["backup-postgres.sh", "backup-data.sh"]
    assert [row["artifact_type"] for row in result["artifacts"]] == ["postgresql", "files"]
    data_script = (Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-data.sh").read_text(encoding="utf-8")
    assert "backup_paths=(uploads)" in data_script
    assert "for optional_path in certs uptime-kuma" in data_script
    assert "BACKUP_RESULT_FILE" in data_script
