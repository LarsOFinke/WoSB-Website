#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.recovery.contract import (  # noqa: E402
    add_report_check,
    finalize_report,
    new_report,
    write_report,
)


def source_artifact(path: Path) -> dict[str, object]:
    path = path.expanduser().resolve()
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    digest = hashlib.sha256()
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError("Recovery source is not a regular file.")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise RuntimeError("Recovery source changed while it was hashed.")
    return {"filename": path.name, "size_bytes": before.st_size, "sha256": digest.hexdigest()}


def read(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Recovery report is invalid.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("report", type=Path)
    create.add_argument("--mode", required=True)
    create.add_argument("--source", required=True)
    create.add_argument("--source-file", type=Path)
    add = sub.add_parser("add")
    add.add_argument("report", type=Path)
    add.add_argument("--name", required=True)
    add.add_argument("--status", required=True, choices=("passed", "failed", "warning", "skipped"))
    add.add_argument("--detail", default="")
    add.add_argument("--data-json", default="")
    finish = sub.add_parser("finish")
    finish.add_argument("report", type=Path)
    finish.add_argument("--status", required=True, choices=("passed", "failed", "aborted"))
    finish.add_argument("--recoverable", choices=("true", "false"), default="false")
    args = parser.parse_args()

    if args.command == "create":
        artifact = source_artifact(args.source_file) if args.source_file else None
        report = new_report(mode=args.mode, source=args.source, source_artifact=artifact)
    else:
        report = read(args.report)
        if args.command == "add":
            data = json.loads(args.data_json) if args.data_json else None
            if data is not None and not isinstance(data, dict):
                raise RuntimeError("--data-json must contain an object.")
            add_report_check(report, name=args.name, status=args.status, detail=args.detail, data=data)
        else:
            finalize_report(
                report,
                status=args.status,
                recoverable=args.recoverable == "true",
            )
    write_report(args.report, report)
    print(args.report)


if __name__ == "__main__":
    main()
