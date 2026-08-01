from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .automation import executable_path, install_pull_timer, remove_pull_timer
from .config import load_profile, profile_path
from .docker_lab import (
    connection,
    import_check_bundle,
    initialize_lab,
    lab_status,
    remove_lab_data,
    restore_bundle,
    start_lab,
    stop_lab,
    verify_recovery,
)
from .linux_setup import setup_rootless_lab
from .sftp_client import download_latest
from .server_setup import provision_backup_server
from .verification import verify_encrypted_bundle


def _pull(quiet: bool) -> int:
    profile = load_profile().normalized(); profile.validate(require_fingerprint=True)
    if not profile.ssh_key_path:
        raise RuntimeError("Der automatische Linux-Abruf benötigt einen im Profil hinterlegten SSH-Schlüssel.")
    bundle = download_latest(profile)
    result = verify_encrypted_bundle(bundle, Path(profile.age_identity_path))
    if not quiet:
        print(f"OK: {bundle}"); print(f"Version={result.version or 'unknown'} files={result.file_count}"); print(f"SHA256={result.bundle_sha256}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rbf-recovery-tool")
    sub = parser.add_subparsers(dest="command")
    pull = sub.add_parser("pull", help="Neuestes Bundle laden und vollständig prüfen"); pull.add_argument("--quiet", action="store_true")
    verify = sub.add_parser("verify", help="Lokales verschlüsseltes Bundle kryptografisch prüfen"); verify.add_argument("bundle", type=Path); verify.add_argument("--identity", type=Path, required=True)
    recovery = sub.add_parser("recovery", help="Vollständige Wiederherstellbarkeit nachweisen")
    recovery_sub = recovery.add_subparsers(dest="recovery_action", required=True)
    recovery_verify = recovery_sub.add_parser("verify", help="Import, Migration, Schlüssel und API-Readiness prüfen")
    recovery_verify.add_argument("bundle", type=Path); recovery_verify.add_argument("--identity", type=Path, required=True); recovery_verify.add_argument("--repository", type=Path, required=True); recovery_verify.add_argument("--report", type=Path, required=True); recovery_verify.add_argument("--allow-legacy", action="store_true"); recovery_verify.add_argument("--allow-uncoordinated", action="store_true")
    timer = sub.add_parser("timer", help="systemd-Benutzertimer verwalten"); timer.add_argument("action", choices=("install", "remove")); timer.add_argument("--calendar", default="daily")
    setup = sub.add_parser("setup", help="Optionale Linux-Komponenten einrichten"); setup.add_argument("--with-db-lab", action="store_true"); setup.add_argument("--with-timer", action="store_true")
    server = sub.add_parser("server", help="Dedizierten Backup-Server automatisch provisionieren")
    server_sub = server.add_subparsers(dest="server_action", required=True)
    provision = server_sub.add_parser("provision", help="SSH/SFTP-Konto, Verzeichnis und age-Schlüssel einrichten")
    provision.add_argument("request", type=Path); provision.add_argument("--host", required=True); provision.add_argument("--output", type=Path, required=True); provision.add_argument("--identity", type=Path, default=Path.home() / "RBF-Recovery" / "rbf-recovery-identity.txt"); provision.add_argument("--port", type=int, default=22); provision.add_argument("--user", default="rbf-backup"); provision.add_argument("--recovery-user", default="rbf-recovery"); provision.add_argument("--recovery-key", type=Path, default=Path.home() / "RBF-Recovery" / "rbf-recovery-readonly-ed25519"); provision.add_argument("--directory", default="/srv/rbf-backups/wosb"); provision.add_argument("--retention-days", type=int, default=30); provision.add_argument("--allow-from", default=""); provision.add_argument("--skip-package-install", action="store_true"); provision.add_argument("--no-local-profile", action="store_true")
    lab = sub.add_parser("lab", help="Lokales PostgreSQL-Recovery-Labor verwalten")
    lab.add_argument("action", choices=("init", "start", "stop", "status", "restore", "import-check", "remove")); lab.add_argument("--port", type=int, default=55432); lab.add_argument("--bundle", type=Path); lab.add_argument("--identity", type=Path); lab.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if not args.command:
        from .app import main as gui_main
        gui_main(); return 0
    if args.command == "pull": return _pull(args.quiet)
    if args.command == "verify":
        result = verify_encrypted_bundle(args.bundle, args.identity); print(f"OK: files={result.file_count} sha256={result.bundle_sha256}"); return 0
    if args.command == "recovery":
        result = verify_recovery(args.bundle, args.identity, args.repository, args.report, allow_legacy=args.allow_legacy, allow_uncoordinated=args.allow_uncoordinated)
        print(f"recoverable={str(result.recoverable).lower()} compatibility={result.compatibility} report={result.report}"); return 0
    if args.command == "timer":
        install_pull_timer(args.calendar) if args.action == "install" else remove_pull_timer(); return 0
    if args.command == "server":
        result = provision_backup_server(
            args.request,
            host=args.host,
            output=args.output,
            identity=args.identity,
            port=args.port,
            username=args.user,
            recovery_username=args.recovery_user,
            recovery_ssh_key=args.recovery_key,
            remote_directory=args.directory,
            allow_from=args.allow_from,
            skip_package_install=args.skip_package_install,
            retention_days=args.retention_days,
            configure_local_profile=not args.no_local_profile,
        )
        print(f"Enrollment-Antwort: {result}")
        print(f"Private age-Identität: {args.identity.expanduser().resolve()}")
        print(f"Lokaler Recovery-Leseschlüssel: {args.recovery_key.expanduser().resolve()}")
        if not args.no_local_profile:
            print(f"Recovery-Profil: {profile_path()}")
            print("Der spätere Abruf funktioniert lokal mit: rbf-recovery-tool pull")
        print("WICHTIG: age-Identität und Recovery-Leseschlüssel zusätzlich verschlüsselt offline sichern.")
        return 0
    if args.command == "setup":
        if not args.with_db_lab and not args.with_timer: raise RuntimeError("Mindestens --with-db-lab oder --with-timer angeben.")
        if args.with_db_lab: setup_rootless_lab(executable_path())
        if args.with_timer: install_pull_timer()
        return 0
    if args.command == "lab":
        if args.action == "init": print(initialize_lab(args.port).safe_summary)
        elif args.action == "start": print(start_lab().safe_summary)
        elif args.action == "stop": stop_lab()
        elif args.action == "status":
            status = lab_status(); print(status.detail)
            if status.configured:
                try: print(connection().safe_summary)
                except RuntimeError: pass
        elif args.action in {"restore", "import-check"}:
            if not args.bundle or not args.identity: raise RuntimeError(f"lab {args.action} benötigt --bundle und --identity.")
            if args.action == "restore": print(restore_bundle(args.bundle, args.identity).safe_summary)
            else:
                if not args.report: raise RuntimeError("lab import-check benötigt --report.")
                result = import_check_bundle(args.bundle, args.identity, args.report); print(f"recoverable=false import_ok=true report={result.report}")
        elif args.action == "remove": remove_lab_data()
        return 0
    return 2


def entrypoint() -> None:
    try: raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr); raise SystemExit(1) from exc
