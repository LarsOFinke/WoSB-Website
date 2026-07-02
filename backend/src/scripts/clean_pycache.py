from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PYTHON_CACHE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_DIR_NAMES = {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules"}


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return False
    return any(part in EXCLUDED_DIR_NAMES for part in relative_parts)


def collect_cache_paths(root: Path) -> list[Path]:
    root = root.resolve()
    cache_paths: list[Path] = []

    for path in root.rglob("*"):
        if _is_excluded(path, root):
            continue

        if path.is_dir() and path.name == "__pycache__":
            cache_paths.append(path)
            continue

        if path.is_file() and path.suffix in PYTHON_CACHE_SUFFIXES:
            cache_paths.append(path)

    return sorted(cache_paths, key=lambda item: (len(item.parts), str(item)))


def delete_cache_paths(paths: list[Path]) -> tuple[int, int]:
    deleted_dirs = 0
    deleted_files = 0

    # Delete files first, then directories. Directories may contain files not matched separately.
    for path in [item for item in paths if item.is_file()]:
        path.unlink(missing_ok=True)
        deleted_files += 1

    for path in sorted([item for item in paths if item.is_dir()], key=lambda item: len(item.parts), reverse=True):
        if path.exists():
            shutil.rmtree(path)
            deleted_dirs += 1

    return deleted_dirs, deleted_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete Python cache files from the WoSB backend.")
    parser.add_argument(
        "--root",
        type=Path,
        default=_backend_root(),
        help="Root directory to clean. Defaults to the backend root.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting anything.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"Root path does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Root path is not a directory: {root}")

    cache_paths = collect_cache_paths(root)

    if args.dry_run:
        if not cache_paths:
            print(f"No Python cache files found under {root}.")
            return

        print(f"Would delete {len(cache_paths)} Python cache path(s) under {root}:")
        for path in cache_paths:
            print(f"- {path}")
        return

    deleted_dirs, deleted_files = delete_cache_paths(cache_paths)
    print(
        "Python cache cleanup complete: "
        f"deleted {deleted_dirs} __pycache__ directorie(s) and {deleted_files} .pyc/.pyo file(s)."
    )


if __name__ == "__main__":
    main()
