#!/usr/bin/env python3
"""Package already-built application images for Git-free target deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile


SERVICES = {
    "api": "rbf-hub-api",
    "secure-api": "rbf-hub-secure-api",
    "gateway": "rbf-hub-gateway",
}
ALIASES = {"python": "api", "java": "secure-api", "frontend": "gateway"}
RECOVERY_CONTRACT_FILES = (
    Path("contracts/__init__.py"),
    Path("contracts/recovery/__init__.py"),
    Path("contracts/recovery/contract.py"),
)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release/application version")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--git-commit", default="", help="optional source revision identifier")
    parser.add_argument("--api-image", default="", help="override the API image reference")
    parser.add_argument("--secure-api-image", default="", help="override the Spring image reference")
    parser.add_argument("--gateway-image", default="", help="override the gateway image reference")
    parser.add_argument("--components", default="api,secure-api,gateway", help="comma-separated components to package")
    args = parser.parse_args()

    components: list[str] = []
    for value in args.components.split(","):
        component = ALIASES.get(value.strip(), value.strip())
        if component not in SERVICES:
            raise SystemExit(f"Unbekannte Komponente: {value}")
        if component not in components:
            components.append(component)
    if not components:
        raise SystemExit("Mindestens eine Komponente ist erforderlich.")
    images = {
        "api": args.api_image or f"{SERVICES['api']}:{args.version}",
        "secure-api": args.secure_api_image or f"{SERVICES['secure-api']}:{args.version}",
        "gateway": args.gateway_image or f"{SERVICES['gateway']}:{args.version}",
    }
    images = {service: images[service] for service in components}
    for service, image in images.items():
        result = subprocess.run(["docker", "image", "inspect", image], capture_output=True)
        if result.returncode:
            raise SystemExit(f"Image für {service} fehlt: {image}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rbf-artifact-") as temporary:
        staging = Path(temporary)
        image_archive = staging / "images.tar"
        run(["docker", "save", "--output", str(image_archive), *images.values()])
        manifest = {
            "schema_version": 1,
            "kind": "rbf-deployment-artifact",
            "version": args.version,
            "git_commit": args.git_commit,
            "components": components,
            "images": images,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        for relative_path in RECOVERY_CONTRACT_FILES:
            source = Path(__file__).resolve().parent.parent / relative_path
            destination = staging / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        checksums = "".join(
            f"{digest(path)}  {path}\n"
            for path in (staging / "manifest.json", image_archive, *[staging / path for path in RECOVERY_CONTRACT_FILES])
        )
        (staging / "SHA256SUMS").write_text(checksums, encoding="ascii")
        output = args.output_dir / f"rbf-deployment-{args.version}.tar.gz"
        with tarfile.open(output, "w:gz") as archive:
            for path in sorted(staging.iterdir()):
                archive.add(path, arcname=str(path.relative_to(staging)), recursive=path.is_dir())
    print(output)
    print(digest(output))


if __name__ == "__main__":
    main()
