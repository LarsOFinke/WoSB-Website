from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.core.maintenance_event_outbox import MaintenanceEventOutbox
from app.db.session import SessionLocal
from app.modules.admin.services.outbound_webhook_delivery_service import (
    attempt_webhook_delivery,
    queue_webhook_event,
)


logger = logging.getLogger(__name__)


def deliver_pending_maintenance_events() -> int:
    """Queue durable host maintenance events and acknowledge only committed rows."""

    outbox = MaintenanceEventOutbox(Path(settings.control_request_dir))
    delivered = 0
    for path in outbox.pending_paths():
        try:
            event = outbox.read(path)
            with SessionLocal() as db:
                delivery_ids = queue_webhook_event(
                    db,
                    event_type=f"system.maintenance.{event.action}",
                    resource_type="system_maintenance",
                    resource_id=event.event_id,
                    resource_url="/admin?section=status",
                    actor=None,
                    scope_type="global",
                    data={
                        "reason": event.reason,
                        "message": event.message,
                        "started_at": event.started_at,
                        "occurred_at": event.occurred_at,
                        "outcome": event.outcome or "running",
                    },
                )
            path.unlink(missing_ok=True)
        except Exception:
            logger.exception("maintenance webhook event queue failed", extra={"path": str(path)})
            continue
        for delivery_id in delivery_ids:
            attempt_webhook_delivery(delivery_id)
        delivered += 1
    return delivered


__all__ = ["deliver_pending_maintenance_events"]
