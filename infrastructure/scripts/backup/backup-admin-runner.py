#!/usr/bin/env python3
from __future__ import annotations

import hashlib  # noqa: F401 - stable runner API for host diagnostics
from pathlib import Path
import socket  # noqa: F401 - compatibility seam for tests and host instrumentation
import subprocess  # noqa: F401 - compatibility seam for tests and host instrumentation
import sys
import threading
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
for import_root in (SCRIPT_DIR, REPOSITORY_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from backup_runner_core import ACTIVE_STATE, RunnerCore, now  # noqa: E402
from backup_runner_enrollment import BackupEnrollmentMixin  # noqa: E402
from backup_runner_restore import BackupRestoreMixin  # noqa: E402
from backup_runner_transfer import BackupTransferMixin  # noqa: E402
from local_backup_catalog import (  # noqa: E402, F401 - stable runner API
    consume_database_restore_approval,
    resolve_local_postgres_backup,
    scan_local_postgres_backups,
)


class Runner(
    BackupEnrollmentMixin,
    BackupTransferMixin,
    BackupRestoreMixin,
    RunnerCore,
):
    def run(self) -> None:
        self.prepare()
        self.request = self.read_json(self.request_file)
        self.request_file.unlink(missing_ok=True)
        operation = str(self.request.get("operation") or "")
        started_at = now()
        self.write_status(
            ACTIVE_STATE,
            "Backup operation is running.",
            started_at=started_at,
            finished_at=None,
        )
        thread = threading.Thread(target=self.heartbeat, daemon=True)
        thread.start()
        try:
            updates: dict[str, Any] = {}
            if operation == "prepare_key":
                updates = self.prepare_key()
                message = "Protected SSH upload key prepared. Install the displayed public key on the backup server."
            elif operation == "prepare_enrollment":
                updates = self.prepare_enrollment()
                message = "Enrollment request created. Provision the backup server with the Recovery Tool."
            elif operation == "apply_enrollment":
                updates = self.apply_enrollment()
                message = "Backup server enrolled, encrypted recovery enabled and SFTP connection verified."
            elif operation == "discover":
                updates = self.discover()
                message = "SSH host key discovered. Verify its fingerprint before saving the connection."
            elif operation == "configure":
                self.configure()
                message = "Remote backup connection saved after a successful SFTP write/read/delete test."
            elif operation == "test":
                self.test_connection()
                message = "Remote SFTP write/read/delete test succeeded."
            elif operation == "backup":
                updates = self.create_and_transfer_backup()
                message = "Database, uploaded-file and any enabled encrypted recovery backups were created, transferred and verified successfully."
            elif operation == "delete_configuration":
                updates = self.delete_configuration()
                message = "Remote backup connection removed."
            elif operation == "scan_local_backups":
                updates = self.scan_local_backups()
                message = "The protected local PostgreSQL backup catalog was refreshed."
            elif operation == "restore_postgresql":
                updates = self.restore_postgresql()
                message = "The selected PostgreSQL backup was restored and the application passed its checks."
            elif operation == "restore_files":
                updates = self.restore_files()
                message = "The selected file modules were restored successfully."
            else:
                raise RuntimeError("Unsupported backup operation.")
            self.write_status(
                "succeeded",
                message,
                started_at=started_at,
                finished_at=now(),
                **updates,
            )
        except Exception as exc:
            self.request.pop("approval_token_sha256", None)
            self.log(f"ERROR: {exc}")
            self.write_status(
                "failed",
                self.public_failure_message(operation),
                started_at=started_at,
                finished_at=now(),
            )
            raise
        finally:
            self.stop_heartbeat.set()
            thread.join(timeout=2)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: backup-admin-runner.py INFRA_DIR CLAIMED_REQUEST", file=sys.stderr
        )
        return 2
    runner = Runner(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
