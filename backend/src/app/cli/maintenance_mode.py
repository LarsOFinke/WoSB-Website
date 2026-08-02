from __future__ import annotations

import argparse
from pathlib import Path

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
    value.add_argument("--reason", choices=sorted(MAINTENANCE_REASONS), default="manual")
    value.add_argument("--message")
    value.add_argument("--retry-after", type=int, default=120)
    return value


def main() -> None:
    args = parser().parse_args()
    service = ServiceAvailability(args.status_dir)
    if args.action == "enable":
        state = service.enable(
            reason=args.reason,
            message=args.message or DEFAULT_MESSAGES[args.reason],
            retry_after_seconds=args.retry_after,
        )
        print(f"Maintenance mode enabled: {state.reason}")
    elif args.action == "disable":
        print(
            "Maintenance mode disabled." if service.disable() else "Maintenance mode was inactive."
        )
    else:
        state = service.read()
        print("inactive" if state is None else f"active: {state.reason} since {state.started_at}")


if __name__ == "__main__":
    main()
