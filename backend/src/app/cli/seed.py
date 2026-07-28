import argparse
import sys

from app.core.config import settings
from app.db.init_db import create_and_seed, reset_database, seed_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the Royal Blackwater Fleet database.")
    parser.add_argument("--reset", action="store_true", help="Drop all tables before seeding.")
    parser.add_argument(
        "--restore-seed-defaults",
        action="store_true",
        help=(
            "Explicitly discard overrides on repository-owned master data before seeding. "
            "Custom records and user content are not changed."
        ),
    )
    return parser.parse_args()


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{name}={value}" for name, value in counts.items())


def main() -> None:
    args = parse_args()
    if args.reset:
        if args.restore_seed_defaults:
            raise SystemExit("--reset and --restore-seed-defaults cannot be combined.")
        reset_database()
        print("Database reset and seeded.")
        return

    if settings.manages_schema_at_startup:
        summary = create_and_seed(restore_seed_defaults=args.restore_seed_defaults)
    else:
        summary = seed_database(restore_seed_defaults=args.restore_seed_defaults)

    if args.restore_seed_defaults:
        print(f"Repository seed defaults restored: {_format_counts(summary['restored'])}.")
    preserved = summary["preserved"]
    if any(preserved.values()):
        print(
            "Seed completed while preserving repository-owned admin overrides: "
            f"{_format_counts(preserved)}. Use --restore-seed-defaults only when the "
            "versioned repository catalog should become authoritative again.",
            file=sys.stderr,
        )
    print("Database seeded.")


if __name__ == "__main__":
    main()
