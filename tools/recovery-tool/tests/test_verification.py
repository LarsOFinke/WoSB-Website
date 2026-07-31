from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rbf_recovery_tool.config import Profile
from rbf_recovery_tool.verification import generate_identity, verify_plain_archive, verify_sidecar


def _archive(path: Path, *, unsafe: bool = False) -> None:
    files = {
        "artifacts/postgres/rbf.sql.gz": b"postgres",
        "artifacts/files/rbf-files.tar.gz": b"files",
        "configuration/infrastructure.env": b"SECRET=value\n",
        "system/backup-metadata.json": b"{}",
    }
    manifest = {
        "schema_version": 1,
        "created_at": "2026-07-31T00:00:00+00:00",
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
        if unsafe:
            info = tarfile.TarInfo("../escape")
            info.size = 0
            handle.addfile(info, io.BytesIO())


def test_plain_archive_manifest_verification(tmp_path: Path) -> None:
    archive = tmp_path / "recovery.tar.gz"
    _archive(archive)
    result = verify_plain_archive(archive, "a" * 64)
    assert result.version == "1.0.0"
    assert result.file_count == 4
    assert result.bundle_sha256 == "a" * 64


def test_sidecar_and_unsafe_archive_are_rejected(tmp_path: Path) -> None:
    bundle = tmp_path / "rbf-recovery-20260731T000000Z.tar.gz.age"
    bundle.write_bytes(b"encrypted")
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    Path(f"{bundle}.sha256").write_text(f"{digest}  {bundle.name}\n", encoding="ascii")
    assert verify_sidecar(bundle) == digest

    unsafe = tmp_path / "unsafe.tar.gz"
    _archive(unsafe, unsafe=True)
    try:
        verify_plain_archive(unsafe)
    except RuntimeError as exc:
        assert "Unsicherer Pfad" in str(exc)
    else:
        raise AssertionError("Path traversal must be rejected")


def test_profile_contains_no_password_storage() -> None:
    profile = Profile(host="server", username="backup")
    assert "password" not in profile.__dataclass_fields__


def test_generate_identity_uses_bundled_keygen_without_overwriting(
    tmp_path: Path, monkeypatch
) -> None:
    import subprocess
    import rbf_recovery_tool.verification as verification

    executable = tmp_path / "age-keygen.exe"
    executable.write_bytes(b"stub")
    target = tmp_path / "identity.txt"

    def fake_run(command, **kwargs):
        assert command == [str(executable), "-o", str(target.resolve())]
        target.write_text(
            "# public key: age1testpublickey\nAGE-SECRET-KEY-TEST\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(
            command, 0, stdout="Public key: age1testpublickey\n", stderr=""
        )

    monkeypatch.setattr(verification, "locate_age_keygen", lambda: executable)
    monkeypatch.setattr(verification.subprocess, "run", fake_run)
    assert generate_identity(target) == "age1testpublickey"
    assert target.is_file()
    try:
        generate_identity(target)
    except RuntimeError as exc:
        assert "existiert bereits" in str(exc)
    else:
        raise AssertionError("Existing identity files must never be overwritten")


def test_linux_configuration_uses_xdg_directory(tmp_path: Path, monkeypatch) -> None:
    import rbf_recovery_tool.config as config

    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert config.application_directory() == tmp_path / "xdg" / "RBF Recovery Tool"


def test_bundled_age_lookup_accepts_linux_names(tmp_path: Path, monkeypatch) -> None:
    import rbf_recovery_tool.verification as verification

    age = tmp_path / "age"
    keygen = tmp_path / "age-keygen"
    age.write_bytes(b"stub")
    keygen.write_bytes(b"stub")

    def fake_resource(relative: str) -> Path:
        return tmp_path / Path(relative).name

    monkeypatch.setattr(verification, "resource_path", fake_resource)
    assert verification.locate_age() == age
    assert verification.locate_age_keygen() == keygen
