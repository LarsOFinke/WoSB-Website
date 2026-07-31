from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .automation import executable_path, install_pull_timer, remove_pull_timer
from .config import load_profile
from .docker_lab import (
    connection,
    initialize_lab,
    lab_status,
    remove_lab_data,
    restore_bundle,
    start_lab,
    stop_lab,
)
from .linux_setup import setup_rootless_lab
from .sftp_client import download_latest
from .verification import verify_encrypted_bundle


def _pull(quiet: bool) -> int:
    profile = load_profile().normalized()
    profile.validate(require_fingerprint=True)
    if not profile.ssh_key_path:
        raise RuntimeError(
            "Der automatische Linux-Abruf benötigt einen im Profil hinterlegten SSH-Schlüssel."
        )
    bundle = download_latest(profile)
    result = verify_encrypted_bundle(bundle, Path(profile.age_identity_path))
    if not quiet:
        print(f"OK: {bundle}")
        print(f"Version={result.version or 'unknown'} files={result.file_count}")
        print(f"SHA256={result.bundle_sha256}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rbf-recovery-tool")
    sub = parser.add_subparsers(dest="command")
    pull = sub.add_parser("pull", help="Neuestes Bundle laden und vollständig prüfen")
    pull.add_argument("--quiet", action="store_true")
    verify = sub.add_parser("verify", help="Lokales verschlüsseltes Bundle prüfen")
    verify.add_argument("bundle", type=Path)
    verify.add_argument("--identity", type=Path, required=True)
    timer = sub.add_parser("timer", help="systemd-Benutzertimer verwalten")
    timer.add_argument("action", choices=("install", "remove"))
    timer.add_argument("--calendar", default="daily")
    setup = sub.add_parser("setup", help="Optionale Linux-Komponenten einrichten")
    setup.add_argument("--with-db-lab", action="store_true")
    setup.add_argument("--with-timer", action="store_true")
    lab = sub.add_parser("lab", help="Lokales PostgreSQL-Recovery-Labor verwalten")
    lab.add_argument("action", choices=("init", "start", "stop", "status", "restore", "remove"))
    lab.add_argument("--port", type=int, default=55432)
    lab.add_argument("--bundle", type=Path)
    lab.add_argument("--identity", type=Path)
    args = parser.parse_args(argv)

    if not args.command:
        from .app import main as gui_main
        gui_main()
        return 0
    if args.command == "pull":
        return _pull(args.quiet)
    if args.command == "verify":
        result = verify_encrypted_bundle(args.bundle, args.identity)
        print(f"OK: files={result.file_count} sha256={result.bundle_sha256}")
        return 0
    if args.command == "timer":
        if args.action == "install":
            install_pull_timer(args.calendar)
        else:
            remove_pull_timer()
        return 0
    if args.command == "setup":
        if not args.with_db_lab and not args.with_timer:
            raise RuntimeError("Mindestens --with-db-lab oder --with-timer angeben.")
        if args.with_db_lab:
            setup_rootless_lab(executable_path())
        if args.with_timer:
            install_pull_timer()
        return 0
    if args.command == "lab":
        if args.action == "init":
            print(initialize_lab(args.port).safe_summary)
        elif args.action == "start":
            print(start_lab().safe_summary)
        elif args.action == "stop":
            stop_lab()
        elif args.action == "status":
            status = lab_status()
            print(status.detail)
            if status.configured:
                try:
                    print(connection().safe_summary)
                except RuntimeError:
                    pass
        elif args.action == "restore":
            if not args.bundle or not args.identity:
                raise RuntimeError("lab restore benötigt --bundle und --identity.")
            print(restore_bundle(args.bundle, args.identity).safe_summary)
        elif args.action == "remove":
            remove_lab_data()
        return 0
    return 2


def entrypoint() -> None:
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
