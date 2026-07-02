from __future__ import annotations

import argparse

from app.db.seed import seed_database
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the local WoSB database.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables before seeding.")
    args = parser.parse_args()

    with SessionLocal() as db:
        seed_database(db, reset=args.reset)

    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
