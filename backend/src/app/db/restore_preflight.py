from __future__ import annotations

import sys

from sqlalchemy import select

from app.core.secret_box import SecretBoxError, webhook_secret_box
from app.db.schema_health import current_alembic_heads, expected_alembic_heads
from app.db.session import SessionLocal
from app.modules.admin.models.outbound_webhook import OutboundWebhook
from app.modules.raid_helper.models.raid_helper import RaidHelperProfile


def main() -> int:
    failures = 0
    checked = 0
    with SessionLocal() as db:
        connection = db.connection()
        current = set(current_alembic_heads(connection))
        expected = set(expected_alembic_heads())
        if current != expected:
            print("RBF_RESTORE_PREFLIGHT|schema_mismatch", file=sys.stderr)
            return 2

        for value in db.scalars(select(OutboundWebhook.endpoint_url)):
            if not value:
                continue
            checked += 1
            try:
                webhook_secret_box.decrypt(value)
            except SecretBoxError:
                failures += 1

        for value in db.scalars(select(RaidHelperProfile.api_key_encrypted)):
            if not value:
                continue
            checked += 1
            try:
                webhook_secret_box.decrypt(value)
            except SecretBoxError:
                failures += 1

    if failures:
        print(
            f"RBF_RESTORE_PREFLIGHT|secret_key_mismatch|checked={checked}|failed={failures}",
            file=sys.stderr,
        )
        return 3
    print(f"RBF_RESTORE_PREFLIGHT|ok|checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
