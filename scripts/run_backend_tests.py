#!/usr/bin/env python3
"""Run backend test modules in isolated processes.

The application loads configuration and SQLAlchemy metadata at import time. A
fresh process and runtime directory per module keeps tests deterministic while
remaining intentionally dependency-light.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
TESTS = sorted((BACKEND / "tests").glob("test_*.py"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tests",
        nargs="*",
        help="Optional backend test files relative to backend/, for example tests/test_access_policy.py",
    )
    return parser.parse_args()


def resolve_tests(requested: list[str]) -> list[Path]:
    if not requested:
        return TESTS
    resolved: list[Path] = []
    for value in requested:
        candidate = (BACKEND / value).resolve()
        try:
            candidate.relative_to(BACKEND.resolve())
        except ValueError as exc:
            raise SystemExit(f"Test path leaves backend directory: {value}") from exc
        if not candidate.is_file():
            raise SystemExit(f"Test file not found: {value}")
        resolved.append(candidate)
    return resolved


def main() -> int:
    args = parse_args()
    tests = resolve_tests(args.tests)
    if not tests:
        print("No backend tests found.", file=sys.stderr)
        return 2

    base_environment = os.environ.copy()
    base_environment["PYTHONPATH"] = "src"
    base_environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    started = time.monotonic()
    for test_file in tests:
        relative = test_file.relative_to(BACKEND)
        runtime_root = Path(tempfile.mkdtemp(prefix=f"rbf-{test_file.stem}-"))
        environment = base_environment.copy()
        test_tmp = runtime_root / "tmp"
        test_tmp.mkdir(parents=True, exist_ok=True)
        environment["RBF_TEST_ROOT"] = str(runtime_root)
        environment["TMPDIR"] = str(test_tmp)
        for legacy_name in (
            "RBF_ENV_FILE",
            "RBV_ENV_FILE",
            "BLACKWATER_ENV_FILE",
            "WOSB_ENV_FILE",
        ):
            environment.pop(legacy_name, None)
        module_started = time.monotonic()
        print(f"\n[pytest] {relative}", flush=True)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    str(relative),
                ],
                cwd=BACKEND,
                env=environment,
                check=False,
            )
        finally:
            shutil.rmtree(runtime_root, ignore_errors=True)
        if result.returncode:
            return result.returncode
        print(f"[pytest] passed in {time.monotonic() - module_started:.1f}s", flush=True)

    print(
        f"\nBackend suite passed ({len(tests)} modules, {time.monotonic() - started:.1f}s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
