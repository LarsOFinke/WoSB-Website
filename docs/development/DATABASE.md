# Database development

PostgreSQL is the only production database and Flyway is the sole schema owner.

## Rules

- Add a new immutable `V<version>__<description>.sql` for every schema change.
- Never edit a migration already released.
- Hibernate remains `ddl-auto=validate` and `open-in-view=false`.
- Prefer additive expand/contract changes; delay destructive cleanup.
- Add indexes for filter/sort paths and verify them with realistic query plans.
- Reference-data changes belong to versioned Spring seed resources and must preserve administrative overrides deliberately.

## Verification

`mvn verify` uses PostgreSQL Testcontainers to validate an empty schema, migrations and application startup. Restore tests additionally load a dump into staging and require Flyway plus Spring readiness.

The one-time scripts under `infrastructure/scripts/migration` exist only to adopt the reviewed final schema from installations created before Flyway. They are not a general baseline escape hatch.
