#!/usr/bin/env python3
"""Generate the immutable modular post-V1 Flyway baseline path."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = ROOT / "spring-api/src/main/resources/db/migration"
SOURCE = MIGRATIONS / "V1__current_schema_baseline.sql"
PARTS = (
    ("V3__foundation_and_catalog_schema.sql", "CREATE TABLE build_features", "CREATE TABLE users"),
    ("V4__identity_and_catalog_relations.sql", "CREATE TABLE users", "CREATE TABLE builds"),
    ("V5__domain_aggregate_schema.sql", "CREATE TABLE builds", "CREATE TABLE build_classifications"),
    ("V6__domain_relation_schema.sql", "CREATE TABLE build_classifications", "CREATE UNIQUE INDEX ix_build_features_code"),
    ("V7__schema_indexes.sql", "CREATE UNIQUE INDEX ix_build_features_code", None),
)


def idempotent(sql: str) -> str:
    sql = re.sub(r"(?m)^CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", sql)
    return re.sub(r"(?m)^CREATE (UNIQUE )?INDEX ", r"CREATE \1INDEX IF NOT EXISTS ", sql)


def render(source: str, start: str, end: str | None, filename: str) -> str:
    start_at = source.index(start)
    end_at = len(source) if end is None else source.index(end, start_at)
    body = idempotent(source[start_at:end_at].strip())
    return (
        # Published Flyway files retain their historical header and checksum.
        "-- Generated once from immutable V1 by scripts/migration/"
        "generate_modular_flyway_baseline.py.\n"
        "-- New databases start at B2 and apply this focused schema part. Existing V1 databases\n"
        "-- execute it safely because CREATE TABLE/INDEX statements are idempotent.\n"
        f"-- Migration responsibility: {filename.removeprefix('V').removesuffix('.sql')}.\n\n"
        f"{body}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = SOURCE.read_text(encoding="utf-8")
    stale: list[str] = []
    for filename, start, end in PARTS:
        expected = render(source, start, end, filename)
        target = MIGRATIONS / filename
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != expected:
                stale.append(filename)
        else:
            target.write_text(expected, encoding="utf-8")
    if stale:
        raise SystemExit("Stale modular Flyway migrations: " + ", ".join(stale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
