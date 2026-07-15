#!/usr/bin/env python3
"""Run backend test modules in isolated, time-bounded process groups.

The application loads configuration and SQLAlchemy metadata at import time. A
fresh process and runtime directory per module keeps tests deterministic. A
module timeout also prevents leaked threads or child processes from blocking the
entire CI job after pytest has already finished its assertions.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
TESTS = sorted((BACKEND / "tests").glob("test_*.py"))
DEFAULT_MODULE_TIMEOUT_SECONDS = 300


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tests",
        nargs="*",
        help="Optional backend test files relative to backend/, for example tests/test_access_policy.py",
    )
    parser.add_argument(
        "--module-timeout",
        type=int,
        default=int(
            os.environ.get(
                "RBF_BACKEND_TEST_MODULE_TIMEOUT",
                str(DEFAULT_MODULE_TIMEOUT_SECONDS),
            )
        ),
        help="Maximum seconds per isolated test module (default: 300).",
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


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=5)


def run_module(
    relative: Path,
    *,
    environment: dict[str, str],
    timeout_seconds: int,
) -> int:
    process = subprocess.Popen(
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
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(
            f"[pytest] timeout after {timeout_seconds}s; terminating process group",
            file=sys.stderr,
            flush=True,
        )
        terminate_process_group(process)
        return 124


def main() -> int:
    args = parse_args()
    if args.module_timeout <= 0:
        print("--module-timeout must be greater than zero.", file=sys.stderr)
        return 2
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
            return_code = run_module(
                relative,
                environment=environment,
                timeout_seconds=args.module_timeout,
            )
        finally:
            shutil.rmtree(runtime_root, ignore_errors=True)
        if return_code:
            return return_code
        print(f"[pytest] passed in {time.monotonic() - module_started:.1f}s", flush=True)

    print(
        f"\nBackend suite passed ({len(tests)} modules, {time.monotonic() - started:.1f}s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
