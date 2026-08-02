from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from local_backup_catalog import (
    consume_database_restore_approval,
    resolve_local_postgres_backup,
    scan_local_postgres_backups,
)
from backup_runner_core import now


class BackupRestoreMixin:
    def local_catalog_updates(self) -> dict[str, Any]:
        records, skipped = scan_local_postgres_backups(self.infra_dir)
        return {
            "local_database_backups": [record.public_dict() for record in records],
            "local_catalog_updated_at": now(),
            "local_catalog_skipped_count": skipped,
        }

    def scan_local_backups(self) -> dict[str, Any]:
        self.log("Scanning the protected local PostgreSQL backup directory.")
        updates = self.local_catalog_updates()
        self.log(
            "Verified "
            f"{len(updates['local_database_backups'])} local PostgreSQL backup(s); "
            f"skipped {updates['local_catalog_skipped_count']} invalid entry or entries."
        )
        return updates

    def restore_postgresql(self) -> dict[str, Any]:
        backup_id = str(self.request.get("backup_id") or "")
        approval_token_sha256 = str(self.request.get("approval_token_sha256") or "")
        # Consume host approval before any catalog hashing or gzip work. Every request,
        # including a malformed selection, therefore needs a fresh physical-host action.
        consume_database_restore_approval(self.infra_dir, approval_token_sha256)
        self.request.pop("approval_token_sha256", None)
        record = resolve_local_postgres_backup(self.infra_dir, backup_id)
        if not record.restore_metadata_verified:
            raise RuntimeError(
                "The admin restore path rejects backups without verified restore metadata."
            )
        if not record.production_consistent:
            raise RuntimeError(
                "The admin restore path rejects uncoordinated live snapshots."
            )
        if not record.backup_set_verified:
            raise RuntimeError(
                "The backup is not bound to a validated recovery-tested backup set."
            )
        if record.encryption_keys_compatible is False:
            raise RuntimeError(
                "The selected database backup was created with a different secret-encryption "
                "key ring. Restore the matching full recovery bundle or import the old "
                "WEBHOOK_ENCRYPTION_KEYS before retrying."
            )
        if record.filename.endswith(".gz"):
            preflight = subprocess.run(
                ["gzip", "-t", str(record.path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if preflight.returncode != 0:
                raise RuntimeError(
                    "The selected compressed database backup failed validation."
                )
        self.log(f"Starting approved PostgreSQL restore from {record.filename}.")
        env = os.environ.copy()
        env["RBF_RESTORE_LOCK_HELD"] = "true"
        result = subprocess.run(
            [
                "/usr/bin/env",
                "bash",
                str(self.infra_dir / "scripts/backup/restore-postgres.sh"),
                str(record.path),
            ],
            env=env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=7200,
        )
        for line in (result.stdout or "").splitlines():
            self.log(line)
        if result.returncode != 0:
            raise RuntimeError(
                "The controlled PostgreSQL restore failed; review host logs."
            )
        return self.local_catalog_updates()

    @staticmethod
    def public_failure_message(operation: str) -> str:
        messages = {
            "prepare_key": "The protected SSH upload key could not be prepared.",
            "discover": "SSH host-key discovery failed. Review the protected host log.",
            "configure": "The remote backup connection could not be saved. Review the protected host log.",
            "prepare_enrollment": "The enrollment request could not be created.",
            "apply_enrollment": "The enrollment response could not be applied or verified.",
            "test": "The remote backup connection test failed. Review the protected host log.",
            "backup": "The application backup failed. Review the protected host log.",
            "delete_configuration": "The remote backup connection could not be removed.",
            "scan_local_backups": "The protected local backup catalog could not be refreshed.",
            "restore_postgresql": (
                "The database restore was rejected or failed. Create a new host approval token "
                "if needed and review the protected host log before retrying."
            ),
        }
        return messages.get(operation, "The protected host operation failed.")

    def delete_configuration(self) -> dict[str, Any]:
        if self.secret_dir.exists():
            shutil.rmtree(self.secret_dir)
        self.secret_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.secret_dir, 0o700)
        self.log("Removed the remote backup connection and its private key.")
        return {
            "enrollment_request": None,
            "enrollment_id": None,
            "enrollment_public_key": None,
            "enrollment_applied": False,
        }
