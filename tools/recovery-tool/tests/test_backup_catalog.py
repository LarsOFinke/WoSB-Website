from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import stat
from types import SimpleNamespace
import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rbf_recovery_tool.backup_catalog import remote_backup_catalog  # noqa: E402


def _sidecar(name: str, data: bytes) -> bytes:
    return f"{hashlib.sha256(data).hexdigest()}  {name}\n".encode("ascii")


class FakeSftp:
    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files

    def listdir_attr(self, directory: str):
        prefix = directory.rstrip("/") + "/"
        return [
            SimpleNamespace(
                filename=name.removeprefix(prefix),
                st_size=len(data),
                st_mtime=index + 1,
            )
            for index, (name, data) in enumerate(self.files.items())
            if name.startswith(prefix) and "/" not in name.removeprefix(prefix)
        ]

    def stat(self, path: str):
        return SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_size=len(self.files[path]),
        )

    def open(self, path: str, mode: str):
        assert mode == "rb"
        return io.BytesIO(self.files[path])


def _files() -> dict[str, bytes]:
    root = "/data"
    bundle_name = "rbf-recovery-20260802T010000Z.tar.gz.age"
    report_name = "rbf-postgres-preflight-20260802T010001Z-7.json"
    set_name = "rbf-backup-set-20260802T010002Z-7.json"
    bundle = b"encrypted"
    report = json.dumps(
        {"schema_version": 1, "status": "passed", "recoverable": True}
    ).encode()
    artifacts = {
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
    }
    manifest = json.dumps(
        {
            "schema_version": 1,
            "committed": True,
            "created_at": "2026-08-02T01:00:02+00:00",
            "reason": "scheduled",
            "artifacts": artifacts,
        }
    ).encode()
    return {
        f"{root}/{bundle_name}": bundle,
        f"{root}/{bundle_name}.sha256": _sidecar(bundle_name, bundle),
        f"{root}/{report_name}": report,
        f"{root}/{report_name}.sha256": _sidecar(report_name, report),
        f"{root}/{set_name}": manifest,
        f"{root}/{set_name}.sha256": _sidecar(set_name, manifest),
    }


def test_catalog_reports_committed_recoverable_backup() -> None:
    entries = remote_backup_catalog(FakeSftp(_files()), "/data")

    assert len(entries) == 1
    assert entries[0].status == "successful"
    assert entries[0].recoverable is True
    assert entries[0].reason == "scheduled"
    assert entries[0].artifact_types == ("recovery", "verification")
    assert entries[0].total_size_bytes > 0


def test_catalog_surfaces_incomplete_backup_instead_of_hiding_it() -> None:
    files = _files()
    files.pop("/data/rbf-recovery-20260802T010000Z.tar.gz.age.sha256")

    entries = remote_backup_catalog(FakeSftp(files), "/data")

    assert len(entries) == 1
    assert entries[0].status == "invalid"
    assert "missing artifact" in entries[0].detail
