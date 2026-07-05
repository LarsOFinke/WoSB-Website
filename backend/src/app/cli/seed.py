import argparse

from app.db.init_db import create_and_seed, reset_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the minimal WoSB database.")
    parser.add_argument("--reset", action="store_true", help="Drop all tables before seeding.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.reset:
        reset_database()
        print("Database reset and seeded.")
        return

    create_and_seed()
    print("Database seeded.")


if __name__ == "__main__":
    main()
