from __future__ import annotations

import importlib.util
import base64
import hashlib
from pathlib import Path
import subprocess
import sys


def test_enrollment_preparation_hides_stale_request_until_replacement_is_ready(
    tmp_path, monkeypatch
) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_enrollment_status", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    infra.mkdir()
    (infra / ".env").write_text(
        "DEPLOYMENT_ENVIRONMENT=test\nAPP_HOSTNAME=royal-blackwater-fleet.eu\n"
        "BACKUP_CONTROLLER_WEBSITE_HOST=test.example.net\n",
        encoding="utf-8",
    )
    request = tmp_path / "request.json"
    request.write_text(
        '{"operation":"prepare_enrollment","requested_by":"captain",'
        '"requested_at":"2030-01-15T12:00:00Z","host_capability_sha256":"hash"}',
        encoding="utf-8",
    )
    runner = module.Runner(infra, request)
    statuses: list[tuple[str, dict]] = []

    class Result:
        returncode = 0

    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: Result())
    monkeypatch.setattr(
        runner,
        "write_status",
        lambda state, _message, **updates: statuses.append((state, updates)),
    )
    monkeypatch.setattr(
        runner,
        "prepare_enrollment",
        lambda: {"enrollment_request": {"enrollment_id": "fresh"}},
    )

    runner.run()

    running = next(updates for state, updates in statuses if state == module.ACTIVE_STATE)
    assert running["enrollment_request"] is None
    assert running["enrollment_id"] is None
    assert running["enrollment_public_key"] is None
    assert statuses[-1][1]["enrollment_request"]["enrollment_id"] == "fresh"


def test_enrollment_request_contains_the_exact_deployed_provisioner(
    tmp_path, monkeypatch
) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_embedded_provisioner", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    release = tmp_path / "release"
    infra = release / "infrastructure"
    provisioner_path = release / "tools/backup-server/provision-rbf-backup-server.sh"
    tool_source = release / "tools/recovery-tool/src/rbf_recovery_tool"
    provisioner_path.parent.mkdir(parents=True)
    infra.mkdir()
    (infra / ".env").write_text(
        "DEPLOYMENT_ENVIRONMENT=test\nAPP_HOSTNAME=royal-blackwater-fleet.eu\n"
        "BACKUP_CONTROLLER_WEBSITE_HOST=test.example.net\n",
        encoding="utf-8",
    )
    (release / "VERSION").write_text("1.8.0\n", encoding="utf-8")
    provisioner = b"#!/usr/bin/env bash\nset -Eeuo pipefail\n"
    provisioner_path.write_bytes(provisioner)
    tool_source.mkdir(parents=True)
    (tool_source / "__init__.py").write_text("VERSION = 'test'\n", encoding="utf-8")
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request)
    runner.prepare()
    monkeypatch.setattr(
        runner,
        "_website_host_identity",
        lambda: (
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIWebsiteHostKey=",
            "SHA256:" + "W" * 43,
        ),
    )

    result = runner.prepare_enrollment()["enrollment_request"]

    assert base64.b64decode(result["provisioner_base64"], validate=True) == provisioner
    assert result["provisioner_sha256"] == hashlib.sha256(provisioner).hexdigest()
    recovery_tool = base64.b64decode(result["recovery_tool_base64"], validate=True)
    assert result["recovery_tool_sha256"] == hashlib.sha256(recovery_tool).hexdigest()
    assert result["deployment_environment"] == "test"
    assert result["requested_controller_username"] == "rbf-backup-controller-test"
    assert result["requested_storage_directory"] == "/backups/wosb/test"
    assert result["website_host"] == "test.example.net"


def test_deployment_reconciles_separate_test_and_production_controller_endpoints(
    tmp_path,
) -> None:
    script = (
        Path(__file__).parents[2]
        / "infrastructure/scripts/release/prepare-website-env.sh"
    )
    credentials = tmp_path / "unused-credentials.txt"
    cases = (
        ("test", "test-ssh.example.net", "2222"),
        ("production", "production-ssh.example.net", "22"),
    )
    for environment, host, port in cases:
        env_file = tmp_path / f"{environment}.env"
        env_file.write_text(
            f"DEPLOYMENT_ENVIRONMENT={environment}\n"
            "APP_HOSTNAME=royal-blackwater-fleet.eu\n"
            "BACKUP_CONTROLLER_WEBSITE_HOST=stale.example.net\n"
            "BACKUP_CONTROLLER_WEBSITE_SSH_PORT=2022\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "bash", str(script), str(env_file), str(credentials), environment,
                "", "", "", host, port,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        values = dict(
            line.split("=", 1)
            for line in env_file.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#") and "=" in line
        )
        assert values["DEPLOYMENT_ENVIRONMENT"] == environment
        assert values["BACKUP_CONTROLLER_WEBSITE_HOST"] == host
        assert values["BACKUP_CONTROLLER_WEBSITE_SSH_PORT"] == port


def test_environment_reconciliation_refuses_test_production_repurposing(tmp_path) -> None:
    script = (
        Path(__file__).parents[2]
        / "infrastructure/scripts/release/prepare-website-env.sh"
    )
    env_file = tmp_path / "website.env"
    env_file.write_text("DEPLOYMENT_ENVIRONMENT=test\n", encoding="utf-8")
    result = subprocess.run(
        [
            "bash", str(script), str(env_file), str(tmp_path / "credentials"),
            "production", "production.example.net", "", "admin@example.net",
            "production.example.net", "22",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "cannot be repurposed" in result.stderr
    assert "DEPLOYMENT_ENVIRONMENT=test" in env_file.read_text(encoding="utf-8")


def test_origin_deployment_forwards_controller_host_and_port_per_target() -> None:
    source = (
        Path(__file__).parents[2]
        / "infrastructure/scripts/release/deploy-from-origin.sh"
    ).read_text(encoding="utf-8")
    assert 'RBF_DEPLOY_BACKUP_CONTROLLER_WEBSITE_HOST' in source
    assert 'RBF_DEPLOY_BACKUP_CONTROLLER_WEBSITE_PORT' in source
    assert 'remote_command+=(--backup-controller-website-host "$backup_controller_website_host")' in source
    assert 'remote_command+=(--backup-controller-website-port "$backup_controller_website_port")' in source


def test_managed_controller_account_is_sftp_only() -> None:
    source = (
        Path(__file__).parents[2]
        / "infrastructure/scripts/backup/backup_runner_enrollment.py"
    ).read_text()
    assert "ForceCommand internal-sftp -u 0077 -d /" in source
    assert "AllowTcpForwarding no" in source
    assert "PasswordAuthentication no" in source
    assert "KbdInteractiveAuthentication no" in source
    assert 'f"restrict {public_key}\\n"' in source
    assert 'chroot / "exports"' in source
    assert 'chroot / "requests"' in source


def test_pull_status_artifact_summary_matches_api_contract(tmp_path) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup_runner_transfer.py"
    spec = importlib.util.spec_from_file_location("backup_runner_transfer_contract", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    artifact = tmp_path / "rbf-postgres-example.dump"
    artifact.write_bytes(b"verified backup")
    summary = module.BackupTransferMixin._artifact_summary(
        artifact, "postgresql", f"/exports/{artifact.name}"
    )

    assert summary == {
        "artifact_type": "postgresql",
        "filename": artifact.name,
        "size_bytes": artifact.stat().st_size,
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "remote_path": f"/exports/{artifact.name}",
    }


def test_enrollment_updates_shared_environment_without_replacing_release_symlink(
    tmp_path,
) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_shared_env", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    shared = tmp_path / "shared"
    infra = tmp_path / "releases/1.8.3/infrastructure"
    shared.mkdir()
    infra.mkdir(parents=True)
    shared_env = shared / ".env"
    shared_env.write_text("DEPLOYMENT_ENVIRONMENT=test\n", encoding="utf-8")
    release_env = infra / ".env"
    release_env.symlink_to(shared_env)

    module.Runner._set_env_values(
        release_env,
        {
            "BACKUP_RECOVERY_ENABLED": "true",
            "BACKUP_AGE_RECIPIENT": "age1" + "a" * 58,
        },
    )

    assert release_env.is_symlink()
    assert "BACKUP_RECOVERY_ENABLED=true" in shared_env.read_text(encoding="utf-8")
    assert "BACKUP_AGE_RECIPIENT=age1" in shared_env.read_text(encoding="utf-8")


def test_backup_set_manifest_is_last_file_in_sftp_batch(tmp_path, monkeypatch) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_commit_order", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    infra.mkdir()
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request)
    runner.prepare()
    artifact = tmp_path / "rbf-backup-set-test.json"
    artifact.write_text('{"committed": true}\n', encoding="utf-8")
    checksum = Path(f"{artifact}.sha256")
    import hashlib
    checksum.write_text(f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}\n", encoding="ascii")

    batches: list[str] = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    remote_payloads = {
        artifact.name: artifact.read_bytes(),
        checksum.name: checksum.read_bytes(),
    }

    def fake_run(command, **kwargs):
        if command[0] == "sftp":
            batch = str(kwargs.get("input") or "")
            batches.append(batch)
            for line in batch.splitlines():
                if line.startswith("get "):
                    _, remote_name, destination = line.split(maxsplit=2)
                    Path(destination).write_bytes(remote_payloads[remote_name])
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    runner.transfer(
        {
            "host": "backup.example.net",
            "port": 22,
            "username": "rbf-backup",
            "remote_directory": "/data",
            "managed_server": False,
        },
        artifact,
        "backup_set",
    )
    assert batches
    batch_lines = batches[0].splitlines()
    upload_lines = [line for line in batch_lines if line.startswith(("put ", "rename "))]
    assert upload_lines[-1] == f"rename {artifact.name}.part {artifact.name}"
    assert upload_lines.index(f"rename {checksum.name}.part {checksum.name}") < upload_lines.index(
        f"rename {artifact.name}.part {artifact.name}"
    )
    for source in (checksum, artifact):
        name = source.name
        put_index = batch_lines.index(f"put {source} {name}.part")
        assert batch_lines[put_index + 1] == f"chmod 0640 {name}.part"
        assert batch_lines[put_index + 2] == f"rename {name}.part {name}"


def test_connection_test_requires_sftp_write_read_delete_roundtrip(tmp_path, monkeypatch) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_write_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    infra.mkdir()
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request)
    runner.prepare()
    runner.key_file.write_text("PRIVATE", encoding="utf-8")
    runner.known_hosts_file.write_text("host ssh-ed25519 AAAA\n", encoding="utf-8")

    batches: list[str] = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        assert command[0] == "sftp"
        batch = str(kwargs.get("input") or "")
        batches.append(batch)
        put_line = next(line for line in batch.splitlines() if line.startswith("put "))
        get_line = next(line for line in batch.splitlines() if line.startswith("get "))
        source = Path(put_line.split(maxsplit=2)[1])
        destination = Path(get_line.split(maxsplit=2)[2])
        destination.write_bytes(source.read_bytes())
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    tested_at = runner.test_connection(
        {
            "host": "backup.example.net",
            "port": 22,
            "username": "rbf-backup",
            "remote_directory": "/data",
        },
        persist=False,
    )
    assert tested_at
    assert batches
    batch = batches[0]
    assert "put " in batch
    assert "rename " in batch
    assert "get " in batch
    assert "rm " in batch


def test_transfer_verification_never_requires_remote_shell(tmp_path, monkeypatch) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_sftp_only", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    infra.mkdir()
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request)
    runner.prepare()
    artifact = tmp_path / "backup.sql.gz"
    artifact.write_bytes(b"backup")
    checksum = Path(f"{artifact}.sha256")
    import hashlib
    checksum.write_text(f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}\n", encoding="ascii")
    payloads = {artifact.name: artifact.read_bytes(), checksum.name: checksum.read_bytes()}
    commands: list[str] = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        commands.append(str(command[0]))
        assert command[0] == "sftp"
        batch = str(kwargs.get("input") or "")
        for line in batch.splitlines():
            if line.startswith("get "):
                _, remote_name, destination = line.split(maxsplit=2)
                Path(destination).write_bytes(payloads[remote_name])
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    runner.transfer(
        {
            "host": "backup.example.net",
            "port": 22,
            "username": "rbf-backup",
            "remote_directory": "/data",
            "managed_server": False,
        },
        artifact,
        "postgresql",
    )
    assert commands
    assert set(commands) == {"sftp"}


def test_managed_transfer_requires_backup_server_acceptance_receipt(tmp_path, monkeypatch) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_ingest_receipt", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    infra.mkdir()
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request)
    runner.prepare()
    manifest = tmp_path / "rbf-backup-set-20260822T100000Z-123.json"
    manifest.write_text('{"committed":true}\n', encoding="utf-8")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    Path(f"{manifest}.sha256").write_text(
        f"{digest}  {manifest.name}\n", encoding="ascii"
    )
    batches: list[str] = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        assert command[0] == "sftp"
        batch = str(kwargs.get("input") or "")
        batches.append(batch)
        if "/receipts" in batch:
            get_line = next(line for line in batch.splitlines() if line.startswith("get "))
            destination = Path(get_line.split(maxsplit=2)[2])
            destination.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "rbf-backup-ingest-receipt",
                        "status": "accepted",
                        "manifest": manifest.name,
                        "manifest_sha256": digest,
                    }
                ),
                encoding="utf-8",
            )
        return Result()

    import json
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    runner.transfer(
        {
            "host": "backup.example.net",
            "port": 22,
            "username": "rbf-backup",
            "remote_directory": "/incoming",
            "receipt_directory": "/receipts",
            "managed_server": True,
        },
        manifest,
        "backup_set",
    )

    assert any("cd /incoming" in batch for batch in batches)
    assert any("cd /receipts" in batch for batch in batches)
    assert not any(f"get {manifest.name} " in batch for batch in batches)


def test_prepare_upload_key_exposes_only_public_identity(tmp_path, monkeypatch) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/backup-admin-runner.py"
    spec = importlib.util.spec_from_file_location("backup_runner_key_identity", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    infra.mkdir()
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    runner = module.Runner(infra, request)
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
            return Result(stdout="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestUploadKey=\n")
        if "-lf" in command:
            return Result(stdout="256 SHA256:TestUploadKeyFingerprint test (ED25519)\n")
        raise AssertionError(command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.socket, "gethostname", lambda: "wosb-prod")
    prepared = runner.prepare_key()
    assert prepared["upload_public_key"].startswith("ssh-ed25519 ")
    assert prepared["upload_key_fingerprint"] == "SHA256:TestUploadKeyFingerprint"
    assert "PRIVATE KEY" not in str(prepared)
    assert runner.key_file.is_file()
    assert runner.key_file.stat().st_mode & 0o077 == 0

    summary = runner.connection_summary()
    assert summary["private_key_configured"] is True
    assert summary["upload_public_key"] == prepared["upload_public_key"]
    assert summary["upload_key_fingerprint"] == prepared["upload_key_fingerprint"]
