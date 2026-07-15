from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.fleet.services.fleet_service import get_primary_fleet


def webhook_event_scope(
    db: Session,
    *,
    fleet_id: int | None = None,
    squad_id: int | None = None,
    use_primary_fleet: bool = False,
) -> dict[str, Any]:
    """Return normalized scope metadata used by webhook subscription matching.

    Global subscriptions always receive matching events. Fleet and squad
    subscriptions only receive events that carry the corresponding identifiers,
    so publishers must attach the business scope rather than relying on the
    manual test-delivery path.
    """

    resolved_fleet_id = fleet_id
    if resolved_fleet_id is None and use_primary_fleet:
        primary_fleet = get_primary_fleet(db)
        resolved_fleet_id = primary_fleet.id if primary_fleet is not None else None

    if squad_id is not None:
        return {
            "scope_type": "squad",
            "scope_id": squad_id,
            "fleet_id": resolved_fleet_id,
            "squad_id": squad_id,
        }
    if resolved_fleet_id is not None:
        return {
            "scope_type": "fleet",
            "scope_id": resolved_fleet_id,
            "fleet_id": resolved_fleet_id,
            "squad_id": None,
        }
    return {
        "scope_type": "global",
        "scope_id": None,
        "fleet_id": None,
        "squad_id": None,
    }


__all__ = ["webhook_event_scope"]
