from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
from types import SimpleNamespace
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

import rbf_recovery_tool.sftp_client as sftp_client


def _sidecar(name: str, data: bytes) -> bytes:
    return f"{hashlib.sha256(data).hexdigest()}  {name}\n".encode("ascii")


class FakeSftp:
    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files

    def listdir_attr(self, directory: str):
        prefix = directory.rstrip("/") + "/"
        return [
            SimpleNamespace(filename=name[len(prefix):], st_size=len(data), st_mtime=index + 1)
            for index, (name, data) in enumerate(self.files.items())
            if name.startswith(prefix) and "/" not in name[len(prefix):]
        ]

    def stat(self, path: str):
        data = self.files[path]
        return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_size=len(data))

    def open(self, path: str, mode: str):
        assert mode == "rb"
        return io.BytesIO(self.files[path])


def _committed_files(*, report_recoverable: bool = True) -> dict[str, bytes]:
    root = "/exports"
    bundle_name = "rbf-recovery-20260801T010203Z.tar.gz.age"
    report_name = "rbf-postgres-preflight-20260801T010204Z-42.json"
    set_name = "rbf-backup-set-20260801T010205Z-42.json"
    bundle = b"encrypted-recovery-bundle"
    report = json.dumps(
        {
            "schema_version": 1,
            "mode": "preflight",
            "status": "passed",
            "recoverable": report_recoverable,
        },
        sort_keys=True,
    ).encode("utf-8")
    manifest = json.dumps(
        {
            "schema_version": 1,
            "committed": True,
            "artifacts": {
                "recovery": {
                    "filename": bundle_name,
                    "size_bytes": len(bundle),
                    "sha256": hashlib.sha256(bundle).hexdigest(),
                },
                "verification": {
                    "filename": report_name,
                    "size_bytes": len(report),
                    "sha256": hashlib.sha256(report).hexdigest(),
                },
            },
        },
        sort_keys=True,
    ).encode("utf-8")
    return {
        f"{root}/{bundle_name}": bundle,
        f"{root}/{bundle_name}.sha256": _sidecar(bundle_name, bundle),
        f"{root}/{report_name}": report,
        f"{root}/{report_name}.sha256": _sidecar(report_name, report),
        f"{root}/{set_name}": manifest,
        f"{root}/{set_name}.sha256": _sidecar(set_name, manifest),
    }


def test_latest_bundle_requires_committed_successful_recovery_set() -> None:
    files = _committed_files()
    bundle, size, manifest, report = sftp_client.latest_remote_bundle(FakeSftp(files), "/exports")
    assert bundle == PurePosixPath("/exports/rbf-recovery-20260801T010203Z.tar.gz.age")
    assert size == len(files[str(bundle)])
    assert manifest.name.startswith("rbf-backup-set-")
    assert report.name.startswith("rbf-postgres-preflight-")


def test_latest_bundle_rejects_import_only_or_failed_proof() -> None:
    files = _committed_files(report_recoverable=False)
    try:
        sftp_client.latest_remote_bundle(FakeSftp(files), "/exports")
    except RuntimeError as exc:
        assert "kein durch einen erfolgreichen Recovery-Preflight committedes Bundle" in str(exc)
    else:
        raise AssertionError("A non-recoverable report must not commit a pull bundle")


def test_latest_bundle_rejects_legacy_sidecar_only_export() -> None:
    bundle_name = "rbf-recovery-20260801T010203Z.tar.gz.age"
    bundle = b"legacy"
    files = {
        f"/exports/{bundle_name}": bundle,
        f"/exports/{bundle_name}.sha256": _sidecar(bundle_name, bundle),
    }
    try:
        sftp_client.latest_remote_bundle(FakeSftp(files), "/exports")
    except RuntimeError:
        pass
    else:
        raise AssertionError("A sidecar-only legacy export must not be selected")
