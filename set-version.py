#!/usr/bin/env python3
"""Interactively update the repository's coordinated release version."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def next_version(current: str, choice: str) -> str:
    match = SEMVER.fullmatch(current)
    if not match:
        raise ValueError(f"VERSION is not a three-part SemVer: {current}")
    major, minor, patch = map(int, match.groups())
    if choice == "1":
        patch += 1
    elif choice == "2":
        minor, patch = minor + 1, 0
    elif choice == "3":
        major, minor, patch = major + 1, 0, 0
    else:
        return choice
    return f"{major}.{minor}.{patch}"


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if content.count(old) != 1:
        raise RuntimeError(f"Expected one version marker in {path.relative_to(ROOT)}")
    write_atomically(path, content.replace(old, new, 1))


def write_atomically(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def update_json_version(path: Path, selectors: tuple[str, ...], version: str) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    target = document
    for selector in selectors[:-1]:
        target = target[selector]
    target[selectors[-1]] = version
    write_atomically(path, json.dumps(document, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print(f"Current version: {current}")
    print("1) patch   2) minor   3) major   4) enter an exact version")
    choice = input("Release type [1]: ").strip() or "1"
    if choice not in {"1", "2", "3", "4"}:
        print("Choose 1, 2, 3, or 4.", file=sys.stderr)
        return 2
    requested = input("New version (leave blank for the calculated version): ").strip()
    if choice != "4" and not requested:
        requested = choice
    try:
        version = next_version(current, requested)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    if not SEMVER.fullmatch(version) or version == current:
        print("The new version must be a different three-part SemVer.", file=sys.stderr)
        return 2
    print(f"Update coordinated version {current} -> {version}? [y/N] ", end="")
    if input().strip().lower() not in {"y", "yes"}:
        print("Cancelled.")
        return 0

    replace_once(ROOT / "VERSION", current + "\n", version + "\n")
    replace_once(ROOT / "spring-api/pom.xml", f"<version>{current}</version>", f"<version>{version}</version>")
    update_json_version(ROOT / "frontend/package.json", ("version",), version)
    update_json_version(ROOT / "frontend/package-lock.json", ("version",), version)
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    lock["packages"][""]["version"] = version
    write_atomically(ROOT / "frontend/package-lock.json", json.dumps(lock, indent=2, ensure_ascii=False) + "\n")
    update_json_version(ROOT / "openapi/source/root.json", ("info", "version"), version)

    commands = [
        [sys.executable, "infrastructure/scripts/generation/assemble_openapi.py"],
        [sys.executable, "infrastructure/scripts/generation/generate_api_reference.py"],
        [sys.executable, "infrastructure/scripts/quality/check_repository.py", "--strict-tree"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    print(f"Version updated to {version}. Run `make validate` before release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
