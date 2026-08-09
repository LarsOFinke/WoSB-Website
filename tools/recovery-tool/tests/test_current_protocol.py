from __future__ import annotations

import hashlib
import io
import json
from types import SimpleNamespace
import stat

from rbf_recovery_tool.sftp_client import latest_remote_bundle


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
        return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_size=len(self.files[path]))

    def open(self, path: str, mode: str):
        assert mode == "rb"
        return io.BytesIO(self.files[path])


def _sidecar(name: str, data: bytes) -> bytes:
    return f"{hashlib.sha256(data).hexdigest()}  {name}\n".encode("ascii")


def test_current_spring_flyway_commit_is_pullable() -> None:
    root = "/data"
    bundle_name = "rbf-recovery-20260801T010203Z.tar.gz.age"
    report_name = "rbf-postgres-preflight-20260801T010204Z-42.json"
    set_name = "rbf-backup-set-20260801T010205Z-42.json"
    bundle = b"encrypted-recovery-bundle"
    postgres = b"postgres-dump"
    report = json.dumps(
        {
            "schema_version": 2,
            "mode": "preflight",
            "status": "passed",
            "recoverable": True,
            "source_artifact": {
                "filename": "postgres.dump",
                "size_bytes": len(postgres),
                "sha256": hashlib.sha256(postgres).hexdigest(),
            },
            "checks": [{"name": name, "status": "passed"} for name in (
                "dump_inventory", "staging_database_restore", "flyway_validation",
                "application_readiness", "preflight_cleanup",
            )],
        },
        sort_keys=True,
    ).encode("utf-8")
    manifest = json.dumps(
        {
            "schema_version": 1,
            "committed": True,
            "artifacts": {
                "postgres": {
                    "filename": "postgres.dump",
                    "size_bytes": len(postgres),
                    "sha256": hashlib.sha256(postgres).hexdigest(),
                },
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
    files = {
        f"{root}/{bundle_name}": bundle,
        f"{root}/{bundle_name}.sha256": _sidecar(bundle_name, bundle),
        f"{root}/{report_name}": report,
        f"{root}/{report_name}.sha256": _sidecar(report_name, report),
        f"{root}/{set_name}": manifest,
        f"{root}/{set_name}.sha256": _sidecar(set_name, manifest),
    }

    selected = latest_remote_bundle(FakeSftp(files), root)
    assert selected[0].name == bundle_name
    assert selected[2].name == set_name

