# Database development

PostgreSQL is the only production database and Flyway is the sole schema owner.

## Rules

- Add a new immutable `V<version>__<description>.sql` for every schema change.
- Never edit a migration already released.
- Hibernate remains `ddl-auto=validate` and `open-in-view=false`.
- Prefer additive expand/contract changes; delay destructive cleanup.
- Add indexes for filter/sort paths and verify them with realistic query plans.
- Reference-data changes belong to versioned Spring seed resources and must preserve administrative overrides deliberately.
- Startup seeding repairs system-owned roles and the official fleet while preserving
  marked category, option and ship overrides. An explicit seed restore discards
  those overrides. After seeding, bootstrap-admin initialization idempotently
  ensures an active `fleet_admiral` membership in the official fleet so fleet and
  squad administration do not depend on manual database repair.

## Modular baseline without history rewrites

`V1__current_schema_baseline.sql` has already been applied by deployed systems
and remains byte-for-byte immutable. New empty databases use Flyway's
`B2__modular_schema_baseline.sql` marker, skip the monolithic V1 and apply the
focused V3–V7 schema migrations:

1. foundation and catalog schema;
2. identity and catalog relations;
3. domain aggregate schema;
4. domain relation schema;
5. schema indexes.

Existing V1 databases ignore B2 and apply V3–V7 safely: their table/index
creation is idempotent and therefore preserves all rows and the V1 checksum. The
focused files are generated once from immutable V1 by
`infrastructure/scripts/generation/generate_modular_flyway_baseline.py`; the repository gate
checks their exact content. Future schema work starts at V8 and is authored as a
small immutable migration for one coherent change. Do not regenerate or edit a
published V3–V7 file after release.

## Verification

`mvn verify` uses PostgreSQL Testcontainers to validate an empty schema, migrations and application startup. Restore tests additionally load a dump into staging and require Flyway plus Spring readiness. Migration tests must cover both a fresh B2 path and upgrade from a V1 schema history.

The one-time scripts under `infrastructure/scripts/migration` exist only to adopt the reviewed final schema from installations created before Flyway. They are not a general baseline escape hatch.
