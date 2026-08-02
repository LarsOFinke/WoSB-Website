from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app.core.maintenance_event_outbox import MaintenanceEventOutbox
from app.core.service_availability import MAINTENANCE_REASONS, ServiceAvailability


DEFAULT_MESSAGES = {
    "manual": "Scheduled maintenance is in progress.",
    "restart": "The application is restarting and will be available again shortly.",
    "restore": "A protected database restore is in progress.",
    "update": "A server update is being installed.",
}


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Control the gateway maintenance response.")
    value.add_argument("action", choices=("enable", "disable", "status"))
    value.add_argument("--status-dir", type=Path, required=True)
    value.add_argument("--event-dir", type=Path)
    value.add_argument("--reason", choices=sorted(MAINTENANCE_REASONS), default="manual")
    value.add_argument("--message")
    value.add_argument("--retry-after", type=int, default=120)
    value.add_argument("--outcome", choices=("succeeded", "failed"), default="succeeded")
    return value


def _publish(outbox: MaintenanceEventOutbox, **event: str | None) -> None:
    try:
        outbox.publish(**event)  # type: ignore[arg-type]
    except OSError as exc:
        print(f"Warning: maintenance webhook event could not be persisted: {exc}", file=sys.stderr)


def main() -> None:
    args = parser().parse_args()
    service = ServiceAvailability(args.status_dir)
    outbox = MaintenanceEventOutbox(args.event_dir or args.status_dir.parent / "inbox")
    if args.action == "enable":
        state = service.enable(
            reason=args.reason,
            message=args.message or DEFAULT_MESSAGES[args.reason],
            retry_after_seconds=args.retry_after,
        )
        _publish(
            outbox,
            action="started",
            reason=state.reason,
            message=state.message,
            started_at=state.started_at,
            outcome=None,
        )
        print(f"Maintenance mode enabled: {state.reason}")
    elif args.action == "disable":
        state = service.read()
        disabled = service.disable()
        if disabled and state is not None:
            _publish(
                outbox,
                action="ended",
                reason=state.reason,
                message=args.message or "Maintenance mode ended.",
                started_at=state.started_at,
                outcome=args.outcome,
            )
        print("Maintenance mode disabled." if disabled else "Maintenance mode was inactive.")
    else:
        state = service.read()
        print("inactive" if state is None else f"active: {state.reason} since {state.started_at}")


if __name__ == "__main__":
    main()
