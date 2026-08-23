from __future__ import annotations

import json
import stat
from pathlib import Path

from rbf_recovery_tool.config import Profile, RecoveryConfig, load_config, save_config, save_profile


def _profile(tmp_path: Path, host: str, target: str) -> Profile:
    key = tmp_path / f"{host}.key"
    key.write_text("private", encoding="utf-8")
    identity = tmp_path / f"{host}.age"
    identity.write_text("identity", encoding="utf-8")
    return Profile(
        host=host,
        username=f"rbf-backup-controller-{target}",
        destination_directory=str(tmp_path / host),
        ssh_key_path=str(key),
        age_identity_path=str(identity),
        host_fingerprint="SHA256:" + "A" * 43,
    )


def test_test_and_production_profiles_are_saved_independently(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_profile(_profile(tmp_path, "test-backup.example", "test"), "test")
    save_profile(_profile(tmp_path, "production-backup.example", "production"), "production")

    config = load_config()
    assert config.profile("test").host == "test-backup.example"
    assert config.profile("production").host == "production-backup.example"
    assert config.active_target == "production"


def test_legacy_single_profile_is_imported_as_test_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config" / "RBF Recovery Tool" / "profiles.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"host": "legacy.example", "username": "rbf-recovery"}),
        encoding="utf-8",
    )

    config = load_config()
    assert config.migrated_legacy is True
    assert config.profile("test").host == ""
    assert config.profile("test").username == ""
    assert config.profile("production").host == ""


def test_config_file_is_private(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_config(RecoveryConfig())
    assert stat.S_IMODE((tmp_path / "config" / "RBF Recovery Tool" / "profiles.json").stat().st_mode) == 0o600


def test_legacy_controller_username_requires_fresh_target_enrollment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config" / "RBF Recovery Tool" / "profiles.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "schema_version": 2,
        "active_target": "test",
        "profiles": {
            "test": {"host": "test.example", "username": "rbf-backup-controller"},
            "production": {"host": "prod.example", "username": "rbf-backup-controller"},
        },
    }), encoding="utf-8")

    config = load_config()
    assert config.profile("test").host == ""
    assert config.profile("test").username == ""
    assert config.profile("production").host == ""
    assert config.profile("production").username == ""
