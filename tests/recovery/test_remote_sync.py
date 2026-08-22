from __future__ import annotations

import importlib.util
from pathlib import Path
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


def test_scheduled_remote_sync_publishes_commit_marker_last(tmp_path, monkeypatch) -> None:
    module_path = Path(__file__).parents[2] / "infrastructure/scripts/backup/sync-backup-set-remote.py"
    spec = importlib.util.spec_from_file_location("remote_sync_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    infra = tmp_path / "infrastructure"
    artifact_root = infra / "data"
    artifact_root.mkdir(parents=True)
    artifacts = {}
    for name in ("postgres", "files", "verification", "set", "recovery"):
        path = artifact_root / name
        path.write_bytes(name.encode())
        artifacts[name] = path

    transferred: list[str] = []

    class FakeRunner:
        def __init__(self, _infra, _request):
            self.config_file = tmp_path / "config.json"
            self.key_file = tmp_path / "key"
            self.known_hosts_file = tmp_path / "known_hosts"
            for path in (self.config_file, self.key_file, self.known_hosts_file):
                path.write_text("x", encoding="utf-8")

        def prepare(self):
            return None

        def load_connection(self):
            return {"remote_directory": "/data"}

        def test_connection(self, _config):
            return None

        def transfer(self, _config, path, artifact_type):
            transferred.append(artifact_type)
            return {
                "artifact_type": artifact_type,
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": "a" * 64,
                "remote_path": f"/data/{path.name}",
            }

    monkeypatch.setattr(module, "_load_runner", lambda _root: FakeRunner)
    monkeypatch.setattr(
        module,
        "_load_manifest_validator",
        lambda _infra: lambda root, manifest: {
            "artifacts": {
                "postgres": {"path": str(artifacts["postgres"].relative_to(infra))},
                "files": {"path": str(artifacts["files"].relative_to(infra))},
                "verification": {"path": str(artifacts["verification"].relative_to(infra))},
                "recovery": {"path": str(artifacts["recovery"].relative_to(infra))},
            }
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sync",
            "--infra", str(infra),
            "--postgres", str(artifacts["postgres"]),
            "--files", str(artifacts["files"]),
            "--verification", str(artifacts["verification"]),
            "--set", str(artifacts["set"]),
            "--recovery", str(artifacts["recovery"]),
        ],
    )
    assert module.main() == 0
    assert transferred == ["postgresql", "files", "recovery", "verification", "backup_set"]


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
