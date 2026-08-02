from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.retention import purge_expired_records
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.services.auth_service import delete_expired_sessions
from app.modules.admin.services.outbound_webhook_delivery_service import (
    recover_pending_webhook_deliveries,
)
from app.modules.admin.services.outbound_webhook_service import (
    encrypt_legacy_webhook_endpoints,
)
from app.modules.admin.services.system_update_webhook_service import (
    deliver_pending_system_update_result,
)

logger = logging.getLogger(__name__)


def run_maintenance_once() -> dict[str, int]:
    now = utc_now()
    with SessionLocal() as db:
        expired_sessions = delete_expired_sessions(db, commit=False)
        encrypted_webhooks = encrypt_legacy_webhook_endpoints(db, commit=False)
        removed = purge_expired_records(
            db,
            now=now,
            policy=settings.maintenance,
        )
        db.commit()
    update_webhooks = deliver_pending_system_update_result()
    return {
        "expired_sessions": int(expired_sessions or 0),
        "encrypted_webhooks": int(encrypted_webhooks or 0),
        "system_update_webhooks": int(update_webhooks or 0),
        **removed,
    }


async def maintenance_loop() -> None:
    interval_seconds = max(1, settings.maintenance.interval_hours) * 60 * 60
    # Let the server publish readiness before potentially expensive retention
    # queries or outbound webhook attempts start.
    await asyncio.sleep(60)
    while True:
        try:
            await asyncio.to_thread(run_maintenance_once)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("periodic maintenance failed")
        await asyncio.sleep(interval_seconds)


async def _recover_webhook_deliveries(*, stale_after_seconds: int) -> None:
    try:
        recovered = await asyncio.to_thread(
            recover_pending_webhook_deliveries,
            stale_after_seconds=stale_after_seconds,
        )
        if recovered:
            logger.info(
                "recovered pending outbound webhook deliveries",
                extra={"delivery_count": recovered},
            )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("outbound webhook delivery recovery failed")


async def webhook_delivery_recovery_loop() -> None:
    await _recover_webhook_deliveries(stale_after_seconds=0)
    while True:
        await asyncio.sleep(5 * 60)
        await asyncio.to_thread(deliver_pending_system_update_result)
        await _recover_webhook_deliveries(stale_after_seconds=5 * 60)
