from __future__ import annotations

from typing import Any


def maintenance_samples(common_event: dict[str, Any]) -> dict[str, dict[str, Any]]:
    common = {
        **common_event,
        "scope_type": "global",
        "scope_id": None,
        "fleet_id": None,
        "resource_type": "system_maintenance",
        "resource_url": "/admin?section=status",
    }
    return {
        "system.maintenance.started": {
            **common,
            "resource_id": "maintenance-start-sample",
            "data": {
                "reason": "update",
                "message": "A server update is being installed.",
                "started_at": "2026-08-15T12:00:10+00:00",
                "occurred_at": "2026-08-15T12:00:10+00:00",
                "outcome": "running",
            },
        },
        "system.maintenance.ended": {
            **common,
            "resource_id": "maintenance-end-sample",
            "data": {
                "reason": "update",
                "message": "Maintenance completed successfully.",
                "started_at": "2026-08-15T12:00:10+00:00",
                "occurred_at": "2026-08-15T12:04:30+00:00",
                "outcome": "succeeded",
            },
        },
    }
