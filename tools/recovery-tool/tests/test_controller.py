from __future__ import annotations

import json
from pathlib import Path

from rbf_recovery_tool import controller
from rbf_recovery_tool.config import Profile


def profile(tmp_path: Path) -> Profile:
    key = tmp_path / "key"
    identity = tmp_path / "age.txt"
    key.write_text("private", encoding="utf-8")
    identity.write_text("AGE-SECRET-KEY-test", encoding="utf-8")
    return Profile(
        host="website.example",
        username="rbf-backup-controller-test",
        remote_directory="/exports",
        destination_directory=str(tmp_path / "backups"),
        ssh_key_path=str(key),
        age_identity_path=str(identity),
        host_fingerprint="SHA256:" + "A" * 43,
        enrollment_id="E" * 32,
        target="test",
    )


def test_sync_is_quiet_before_the_first_export(tmp_path, monkeypatch) -> None:
    target = profile(tmp_path)
    monkeypatch.setattr(controller, "_set_names", lambda *_args: set())

    assert controller.sync_latest(target, allow_empty=True) is None


def test_sync_reacknowledges_a_locally_verified_set_without_downloading(
    tmp_path, monkeypatch
) -> None:
    target = profile(tmp_path)
    destination = Path(target.destination_directory)
    destination.mkdir()
    set_name = "rbf-backup-set-20260822T120000Z-123.json"
    bundle = destination / "rbf-recovery-20260822T120000Z.tar.gz.age"
    manifest = destination / set_name
    bundle.write_bytes(b"encrypted")
    manifest.write_text(
        json.dumps({"artifacts": {"recovery": {"filename": bundle.name}}}),
        encoding="utf-8",
    )
    controller._remember_verified(manifest)
    acknowledged: list[Path] = []
    monkeypatch.setattr(controller, "_set_names", lambda *_args: {set_name})
    monkeypatch.setattr(
        controller, "_acknowledge", lambda _profile, path, **_kwargs: acknowledged.append(path)
    )
    monkeypatch.setattr(
        controller,
        "download_latest_with_proof",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("downloaded twice")),
    )

    assert controller.sync_latest(target) == bundle
    assert acknowledged == [manifest]


def test_sync_downloads_and_acknowledges_only_the_newest_set(tmp_path, monkeypatch) -> None:
    target = profile(tmp_path)
    older = "rbf-backup-set-20260822T120000Z-123.json"
    newest = "rbf-backup-set-20260823T120000Z-456.json"
    downloaded: list[str | None] = []
    acknowledged: list[Path] = []

    def download(_profile, *, set_filename=None, **_kwargs):
        downloaded.append(set_filename)
        selected = set_filename or newest
        bundle = Path(target.destination_directory) / "rbf-recovery-new.tar.gz.age"
        manifest = Path(target.destination_directory) / selected
        Path(target.destination_directory).mkdir(parents=True, exist_ok=True)
        bundle.write_bytes(b"encrypted")
        manifest.write_text(
            json.dumps({"artifacts": {"recovery": {"filename": bundle.name}}}),
            encoding="utf-8",
        )
        return bundle, manifest

    monkeypatch.setattr(controller, "_set_names", lambda *_args: {older, newest})
    monkeypatch.setattr(controller, "download_latest_with_proof", download)
    monkeypatch.setattr(controller, "verify_encrypted_bundle", lambda *_args: None)
    monkeypatch.setattr(
        controller,
        "_acknowledge",
        lambda _profile, path, **_kwargs: acknowledged.append(path),
    )

    assert controller.sync_latest(target).name == "rbf-recovery-new.tar.gz.age"
    # Normal sync lets the SFTP validator select the newest complete set and
    # fall back to an older committed set if the newest manifest is incomplete.
    assert downloaded == [None]
    assert [path.name for path in acknowledged] == [newest]
