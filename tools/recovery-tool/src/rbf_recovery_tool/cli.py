from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .automation import install_pull_timer, remove_pull_timer
from .backup_catalog import fetch_backup_catalog
from .config import (
    TARGETS,
    Profile,
    RecoveryConfig,
    load_config,
    load_profile,
    save_config,
    save_profile,
    target_label,
)
from .enrollment import discover_response, load_response
from .sftp_client import download_latest, fetch_host_fingerprint
from .verification import verify_encrypted_bundle


def _target(value: str) -> str:
    if value not in TARGETS:
        raise argparse.ArgumentTypeError("target must be test or production")
    return value


def _profile_from_response(args: argparse.Namespace) -> Profile:
    target = args.target
    response_path = args.response or discover_response()
    response = load_response(response_path)
    args.response = response_path
    profile = load_profile(target)
    if args.local_backup_host:
        host = "127.0.0.1"
        username = response.get("recovery_username") or "rbf-recovery"
    else:
        host = response["host"]
        username = response["username"]
    profile.host = args.host or host
    profile.port = args.port or int(response["port"])
    profile.username = args.username or username
    profile.remote_directory = args.remote_directory or response["remote_directory"]
    profile.host_fingerprint = response["host_key_fingerprint"]
    profile.enrollment_id = response["enrollment_id"]
    if args.ssh_key:
        profile.ssh_key_path = str(Path(args.ssh_key).expanduser())
    if args.identity:
        profile.age_identity_path = str(Path(args.identity).expanduser())
    if args.destination:
        profile.destination_directory = str(Path(args.destination).expanduser())
    return profile.normalized()


def _legacy_secret(candidate: Path, current: str) -> str:
    if Path(current).is_file():
        return current
    return str(candidate) if candidate.is_file() else current


def _setup(args: argparse.Namespace) -> int:
    profile = _profile_from_response(args)
    profile.ssh_key_path = _legacy_secret(
        Path.home() / "RBF-Recovery" / "rbf-recovery-readonly-ed25519", profile.ssh_key_path
    )
    profile.age_identity_path = _legacy_secret(
        Path.home() / "RBF-Recovery" / "rbf-recovery-identity.txt", profile.age_identity_path
    )
    profile.validate(require_fingerprint=True, require_files=True)
    if not args.offline:
        actual = fetch_host_fingerprint(profile)
        if actual != profile.host_fingerprint:
            raise RuntimeError(
                "Live SSH host key does not match the enrollment response. "
                "Do not continue until the change is independently verified."
            )
    path = save_profile(profile, args.target)
    mode = "local backup-host access" if args.local_backup_host else "remote access"
    print(f"Configured {target_label(args.target)} recovery target ({mode}).")
    print(f"Enrollment response: {Path(args.response).expanduser().resolve()}")
    print(f"Profile store: {path}")
    print(f"Pinned host key: {profile.host_fingerprint}")
    if args.offline:
        print("WARNING: live host-key verification was skipped; run `test` before pulling.")
    print(f"Next step: rbf-recovery-tool pull --target {args.target}")
    return 0


def _profile_for(args: argparse.Namespace, *, files: bool = False) -> Profile:
    profile = load_profile(args.target).normalized()
    profile.validate(require_fingerprint=True, require_files=files)
    return profile


def _pull(args: argparse.Namespace) -> int:
    profile = _profile_for(args, files=True)
    bundle = download_latest(profile, password=args.password or "")
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
        description="Pull and verify Spring/Flyway recovery bundles from a pinned backup target.",
    )
    sub = parser.add_subparsers(dest="command")
    setup = sub.add_parser("setup", help="Import one enrollment response into a named target")
    setup.add_argument("--target", required=True, type=_target)
    setup.add_argument(
        "--response", type=Path,
        help="Provisioning response JSON; defaults to the single valid response in ~/Downloads",
    )
    setup.add_argument("--ssh-key", type=Path, help="Private read-only recovery SSH key")
    setup.add_argument("--identity", type=Path, help="Private age identity")
    setup.add_argument("--destination", type=Path, help="Local backup destination")
    setup.add_argument("--host", help="Override response host, e.g. 127.0.0.1")
    setup.add_argument("--port", type=int, help="Override response SSH port")
    setup.add_argument("--username", help="Override response SSH user")
    setup.add_argument("--remote-directory", help="Override the SFTP directory")
    setup.add_argument(
        "--local-backup-host",
        action="store_true",
        help="Use the provisioned loopback-only rbf-recovery account on this backup host",
    )
    setup.add_argument(
        "--offline",
        action="store_true",
        help="Save without a live host-key check; the pinned fingerprint is still required",
    )
    targets = sub.add_parser("targets", help="List configured test and production targets")
    for command in ("pull", "catalog", "verify"):
        target_parser = sub.add_parser(command, help=f"{command.title()} a recovery target")
        target_parser.add_argument("--target", type=_target, default=load_config().active_target)
        target_parser.add_argument("--password", help="SSH key passphrase (never stored)")
        if command == "pull":
            target_parser.add_argument("--quiet", action="store_true")
        elif command == "catalog":
            target_parser.add_argument("--json", action="store_true", dest="as_json")
        else:
            target_parser.add_argument("bundle", type=Path)
            target_parser.add_argument("--identity", type=Path)
    check = sub.add_parser("test", help="Verify the live SSH host key for a target")
    check.add_argument("--target", type=_target, default=load_config().active_target)
    timer = sub.add_parser("timer", help="Manage the Linux automatic pull timer")
    timer.add_argument("action", choices=("install", "remove"))
    timer.add_argument("--target", type=_target, required=True)
    timer.add_argument("--calendar", default="daily")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        from .app import main as gui_main

        gui_main()
        return 0
    if args.command == "setup":
        return _setup(args)
    if args.command == "targets":
        return _show_targets(args)
    if args.command == "pull":
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
        print(f"OK: {target_label(args.target)} host key {actual}")
        return 0
    if args.command == "timer":
        if args.action == "install":
            service, timer = install_pull_timer(args.target, args.calendar)
            print(f"Enabled {target_label(args.target)} timer: {service} / {timer}")
        else:
            remove_pull_timer(args.target)
            print(f"Removed {target_label(args.target)} timer.")
        return 0
    return 2


def entrypoint() -> None:
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
