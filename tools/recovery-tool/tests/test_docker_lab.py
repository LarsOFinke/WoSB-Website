from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tarfile

import yaml

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

import rbf_recovery_tool.docker_lab as docker_lab
import rbf_recovery_tool.verification as verification


def _recovery_archive(path: Path) -> None:
    files = {
        "artifacts/postgres/rbf.sql.gz": b"database",
        "artifacts/files/rbf-files.tar.gz": b"files",
        "configuration/infrastructure.env": b"SECRET=value\n",
    }
    manifest = {
        "schema_version": 1,
        "created_at": "2026-08-01T00:00:00+00:00",
        "application": {"version": "1.0.0"},
        "artifacts": {
            "postgres": "artifacts/postgres/rbf.sql.gz",
            "files": "artifacts/files/rbf-files.tar.gz",
            "configuration": "configuration",
        },
        "files": [
            {
                "path": name,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in files.items()
        ],
    }
    with tarfile.open(path, "w:gz") as handle:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            handle.addfile(info, io.BytesIO(content))
        payload = json.dumps(manifest).encode()
        info = tarfile.TarInfo("manifest.json")
        info.size = len(payload)
        handle.addfile(info, io.BytesIO(payload))


def test_lab_configuration_is_loopback_only_and_secret_minimal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(docker_lab, "application_data_root", lambda: tmp_path)
    first = docker_lab.initialize_lab(55432)
    compose = docker_lab.compose_path().read_text(encoding="utf-8")
    assert '"127.0.0.1:${POSTGRES_LOCAL_PORT}:5432"' in compose
    assert "0.0.0.0" not in compose
    assert "no-new-privileges:true" in compose
    assert "read_only: true" in compose
    assert "driver: local" in compose
    parsed = yaml.safe_load(compose)
    assert parsed["services"]["postgres"]["healthcheck"]["test"] == [
        "CMD-SHELL",
        'pg_isready -U "$${POSTGRES_USER}" -d "$${POSTGRES_DB}"',
    ]
    assert first.password not in compose
    assert stat.S_IMODE(docker_lab.env_path().stat().st_mode) == 0o600
    second = docker_lab.initialize_lab(55432)
    assert second.password == first.password


def test_postgres_artifact_extraction_verifies_bundle_first(tmp_path: Path, monkeypatch) -> None:
    plain = tmp_path / "plain.tar.gz"
    _recovery_archive(plain)
    bundle = tmp_path / "rbf-recovery-20260801T000000Z.tar.gz.age"
    bundle.write_bytes(b"encrypted")
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    Path(f"{bundle}.sha256").write_text(f"{digest}  {bundle.name}\n", encoding="ascii")
    identity = tmp_path / "identity.txt"
    identity.write_text("AGE-SECRET-KEY-TEST\n", encoding="utf-8")

    def fake_decrypt(_bundle: Path, _identity: Path, output: Path) -> None:
        output.write_bytes(plain.read_bytes())

    monkeypatch.setattr(verification, "decrypt_bundle", fake_decrypt)
    extracted = verification.extract_postgres_artifact(bundle, identity, tmp_path / "output")
    assert extracted.name == "rbf.sql.gz"
    assert extracted.read_bytes() == b"database"
    if os.name != "nt":
        assert stat.S_IMODE(extracted.stat().st_mode) == 0o600


def test_systemd_timer_uses_xdg_config_and_requires_key(tmp_path: Path, monkeypatch) -> None:
    import rbf_recovery_tool.automation as automation
    from rbf_recovery_tool.config import Profile

    identity = tmp_path / "identity.txt"
    identity.write_text("key", encoding="utf-8")
    ssh_key = tmp_path / "id_ed25519"
    ssh_key.write_text("key", encoding="utf-8")
    profile = Profile(
        host="server",
        username="backup",
        ssh_key_path=str(ssh_key),
        age_identity_path=str(identity),
        host_fingerprint="SHA256:" + "A" * 43,
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(automation, "load_profile", lambda: profile)
    monkeypatch.setattr(automation, "executable_path", lambda: Path("/opt/rbf recovery/tool"))
    monkeypatch.setattr(automation.shutil, "which", lambda name: "/usr/bin/systemctl")
    calls = []
    monkeypatch.setattr(
        automation.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command),
    )
    service, timer = automation.install_pull_timer("daily")
    assert service.parent == tmp_path / "config" / "systemd" / "user"
    assert 'ExecStart="/opt/rbf recovery/tool" pull --quiet' in service.read_text()
    assert "RandomizedDelaySec=15m" in timer.read_text()
    assert calls[-1][-2:] == ["--now", "rbf-recovery-pull.timer"]
