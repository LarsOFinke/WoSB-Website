from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


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

    def fake_run(command, **kwargs):
        if command[0] == "sftp":
            batches.append(str(kwargs.get("input") or ""))
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
    upload_lines = [line for line in batches[0].splitlines() if line.startswith(("put ", "rename "))]
    assert upload_lines[-1] == f"rename {artifact.name}.part {artifact.name}"
    assert upload_lines.index(f"rename {checksum.name}.part {checksum.name}") < upload_lines.index(
        f"rename {artifact.name}.part {artifact.name}"
    )
