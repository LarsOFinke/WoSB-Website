from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .backup_catalog import fetch_backup_catalog
from .config import (
    TARGETS,
    Profile,
    load_config,
    load_profile,
    target_label,
)
from .controller import sync_latest
from .sftp_client import connect, fetch_host_fingerprint
from .verification import verify_encrypted_bundle


def _target(value: str) -> str:
    if value not in TARGETS:
        raise argparse.ArgumentTypeError("target must be test or production")
    return value


def _profile_for(args: argparse.Namespace, *, files: bool = False) -> Profile:
    profile = load_profile(args.target).normalized()
    profile.validate_target(args.target)
    profile.validate(require_fingerprint=True, require_files=files)
    return profile


def _pull(args: argparse.Namespace) -> int:
    profile = _profile_for(args, files=True)
    bundle = sync_latest(
        profile,
        password=args.password or "",
        trigger=bool(getattr(args, "trigger", False)),
        allow_empty=args.command == "sync",
    )
    if bundle is None:
        return 0
    result = verify_encrypted_bundle(bundle, Path(profile.age_identity_path))
    if not args.quiet:
        print(f"OK: {bundle}")
        print(f"Target={target_label(args.target)}")
        print(f"Release={result.version or 'unknown'} artifact={result.release_artifact}")
        print(f"Files={result.file_count} SHA256={result.bundle_sha256}")
    return 0


def _catalog(args: argparse.Namespace) -> int:
    entries = fetch_backup_catalog(_profile_for(args, files=True), password=args.password or "")
    if args.as_json:
        print(json.dumps([entry.as_dict() for entry in entries], ensure_ascii=False, indent=2))
    elif not entries:
        print("No committed backup sets found.")
    else:
        for entry in entries:
            size_mib = entry.total_size_bytes / (1024 * 1024)
            print(
                f"{entry.created_at or '-'}  {entry.status:10}  {size_mib:9.1f} MiB  "
                f"Recovery={'yes' if entry.recoverable else 'no'}  {entry.reason}  {entry.filename}"
            )
            if entry.status != "successful":
                print(f"  Problem: {entry.detail}")
    return 0


def _verify(args: argparse.Namespace) -> int:
    profile = load_profile(args.target)
    profile.validate_target(args.target, require_enrollment=False)
    identity = Path(args.identity).expanduser() if args.identity else Path(profile.age_identity_path)
    result = verify_encrypted_bundle(args.bundle, identity)
    print(
        f"OK: target={target_label(args.target)} release={result.version or 'unknown'} "
        f"files={result.file_count} sha256={result.bundle_sha256}"
    )
    return 0


def _show_targets(_args: argparse.Namespace) -> int:
    config = load_config()
    for target in TARGETS:
        profile = config.profile(target)
        configured = bool(profile.host and profile.username and profile.host_fingerprint)
        marker = "active" if config.active_target == target else " "
        print(f"{marker:6} {target:10} {'configured' if configured else 'not configured'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rbf-recovery-tool",
        description="Operate isolated test and production backup targets from the backup server.",
    )
    sub = parser.add_subparsers(dest="command")
    targets = sub.add_parser("targets", help="List configured test and production targets")
    for command in ("run", "sync", "catalog", "verify"):
        target_parser = sub.add_parser(command, help=f"{command.title()} a recovery target")
        target_parser.add_argument("--target", type=_target, default=load_config().active_target)
        target_parser.add_argument("--password", help="SSH key passphrase (never stored)")
        if command in {"run", "sync"}:
            target_parser.add_argument("--quiet", action="store_true")
        elif command == "catalog":
            target_parser.add_argument("--json", action="store_true", dest="as_json")
        else:
            target_parser.add_argument("bundle", type=Path)
            target_parser.add_argument("--identity", type=Path)
    check = sub.add_parser("test", help="Verify the live SSH host key for a target")
    check.add_argument("--target", type=_target, default=load_config().active_target)
    check.add_argument("--password", help="SSH key passphrase (never stored)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        from .app import main as gui_main

        gui_main()
        return 0
    if args.command == "targets":
        return _show_targets(args)
    if args.command in {"run", "sync"}:
        args.trigger = args.command == "run"
        return _pull(args)
    if args.command == "catalog":
        return _catalog(args)
    if args.command == "verify":
        return _verify(args)
    if args.command == "test":
        profile = _profile_for(args)
        actual = fetch_host_fingerprint(profile)
        if actual != profile.host_fingerprint:
            raise RuntimeError(
                f"Host-key mismatch: pinned {profile.host_fingerprint}, live {actual}"
            )
        client = connect(profile, password=args.password or "")
        client.close()
        print(f"OK: {target_label(args.target)} SSH host key and authentication verified ({actual})")
        return 0
    return 2


def entrypoint() -> None:
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
