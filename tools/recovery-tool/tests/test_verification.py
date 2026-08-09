from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tarfile

from rbf_recovery_tool.verification import verify_plain_archive


def test_spring_bundle_requires_exact_release_artifact(tmp_path: Path) -> None:
    archive = tmp_path / "recovery.tar.gz"
    files = {
        "artifacts/postgres/database.dump": b"postgres",
        "artifacts/files/files.tar.gz": b"files",
        "artifacts/release/rbf-release.tar.gz": b"release",
        "configuration/infrastructure.env": b"DEPLOYMENT_ENVIRONMENT=test\n",
        "system/backup-metadata.json": b"{}",
    }
    manifest = {
        "schema_version": 2,
        "kind": "rbf-disaster-recovery-bundle",
        "created_at": "2026-08-01T00:00:00+00:00",
        "application": {"version": "1.2.0"},
        "artifacts": {
            "postgres": "artifacts/postgres/database.dump",
            "files": "artifacts/files/files.tar.gz",
            "release": "artifacts/release/rbf-release.tar.gz",
            "configuration": "configuration",
        },
        "files": [
            {"path": name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ],
    }
    with tarfile.open(archive, "w:gz") as handle:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            handle.addfile(info, io.BytesIO(data))
        data = json.dumps(manifest).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(data)
        handle.addfile(info, io.BytesIO(data))

    result = verify_plain_archive(archive, "a" * 64)
    assert result.version == "1.2.0"
    assert result.release_artifact == "rbf-release.tar.gz"

