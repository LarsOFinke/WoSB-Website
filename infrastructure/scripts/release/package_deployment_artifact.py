#!/usr/bin/env python3
"""Create a source-free deployment bundle from a tested Spring JAR and frontend dist."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_FILES = (
    "VERSION",
    "infrastructure/scripts/release/install-artifact.sh",
    "infrastructure/setup.sh",
    "infrastructure/compose.release.yml",
    "infrastructure/.env.example",
    "infrastructure/nginx/default.conf",
    "infrastructure/nginx/security-headers.conf",
    "infrastructure/nginx/upload-security-headers.conf",
    "infrastructure/docker/api-runtime.Dockerfile",
    "infrastructure/docker/gateway-runtime.Dockerfile",
)
RUNTIME_DIRS = (
    "infrastructure/config",
    "infrastructure/scripts/backup",
    "infrastructure/scripts/checks",
    "infrastructure/scripts/deployment",
    "infrastructure/scripts/diagnostics",
    "infrastructure/scripts/lib",
    "infrastructure/scripts/migration",
    "infrastructure/scripts/release",
    "infrastructure/scripts/services",
    "infrastructure/scripts/setup",
    "infrastructure/scripts/tls",
    "infrastructure/systemd",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink())


def copy_tree(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"Required runtime directory is missing: {source}")
    shutil.copytree(source, target, dirs_exist_ok=True, symlinks=False,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", ".DS_Store",
                        "package_deployment_artifact.py", "package_release.py"))
    # Runtime shell entrypoints must remain executable even when a checkout
    # lost the executable bit. The artifact verifier preserves this mode.
    for script in target.rglob("*.sh"):
        script.chmod(script.stat().st_mode | 0o111)


def normalize_frontend_permissions(target: Path) -> None:
    for directory in target.rglob("*"):
        if directory.is_dir():
            directory.chmod(0o755)
        elif directory.is_file():
            directory.chmod(0o644)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--frontend-dist", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-revision", default="")
    args = parser.parse_args()

    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if args.version != expected:
        raise SystemExit(f"Version mismatch: argument={args.version}, repository={expected}")
    jar = args.jar.resolve()
    frontend = args.frontend_dist.resolve()
    if not jar.is_file() or jar.stat().st_size < 1024 * 1024:
        raise SystemExit(f"Compiled Spring Boot JAR missing or implausibly small: {jar}")
    if not (frontend / "index.html").is_file():
        raise SystemExit(f"Compiled frontend dist is incomplete: {frontend}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"rbf-deployment-{args.version}.tar.gz"
    with tempfile.TemporaryDirectory(prefix="rbf-release-") as temporary:
        stage = Path(temporary) / "bundle"
        payload = stage / "payload"
        (payload / "artifacts" / "frontend").mkdir(parents=True)
        shutil.copy2(jar, payload / "artifacts" / "rbf-api.jar")
        copy_tree(frontend, payload / "artifacts" / "frontend")
        normalize_frontend_permissions(payload / "artifacts" / "frontend")
        for relative in RUNTIME_FILES:
            source = ROOT / relative
            if not source.is_file():
                raise SystemExit(f"Required runtime file is missing: {source}")
            target = payload / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in RUNTIME_DIRS:
            copy_tree(ROOT / relative, payload / relative)

        inventory = []
        for path in regular_files(payload):
            relative = path.relative_to(stage).as_posix()
            inventory.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256(path)})
        manifest = {
            "schema_version": 2,
            "kind": "rbf-compiled-release",
            "version": args.version,
            "source_revision": args.source_revision,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "minimum_installer_schema": 2,
            "artifacts": {"api": "payload/artifacts/rbf-api.jar", "frontend": "payload/artifacts/frontend"},
            "files": inventory,
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checksum_lines = [f"{entry['sha256']}  {entry['path']}\n" for entry in inventory]
        checksum_lines.append(f"{sha256(stage / 'manifest.json')}  manifest.json\n")
        (stage / "SHA256SUMS").write_text("".join(checksum_lines), encoding="ascii")
        os.chmod(stage / "SHA256SUMS", 0o644)
        with tarfile.open(output, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for path in sorted(stage.iterdir()):
                archive.add(path, arcname=PurePosixPath(path.name), recursive=True)
    checksum = output.with_suffix(output.suffix + ".sha256")
    checksum.write_text(f"{sha256(output)}  {output.name}\n", encoding="ascii")
    print(output)


if __name__ == "__main__":
    main()
