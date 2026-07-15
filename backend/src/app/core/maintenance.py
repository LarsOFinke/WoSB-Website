from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import delete

from app.core.config import settings
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.services.auth_service import delete_expired_sessions
from app.modules.admin.models.app_log import AppLog
from app.modules.admin.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def run_maintenance_once() -> dict[str, int]:
    now = utc_now()
    with SessionLocal() as db:
        expired_sessions = delete_expired_sessions(db, commit=False)
        app_logs = db.execute(
            delete(AppLog).where(
                AppLog.created_at
                < now - timedelta(days=settings.maintenance.app_log_retention_days)
            )
        ).rowcount
        audit_logs = db.execute(
            delete(AuditLog).where(
                AuditLog.created_at
                < now - timedelta(days=settings.maintenance.audit_log_retention_days)
            )
        ).rowcount
        db.commit()
    return {
        "expired_sessions": int(expired_sessions or 0),
        "app_logs": int(app_logs or 0),
        "audit_logs": int(audit_logs or 0),
    }


async def maintenance_loop() -> None:
    interval_seconds = max(1, settings.maintenance.interval_hours) * 60 * 60
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(run_maintenance_once)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("periodic maintenance failed")
