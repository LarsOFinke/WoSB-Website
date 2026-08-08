# API Diagnostics, Flyway Regression, and JSON Modularization – 2026-08-08

## Starting point

The complete Maven test run failed in
`FlywayMigrationCompatibilityTest.upgradesAnExistingV1HistoryWithoutChangingOrReapplyingIt`.
The test expected five migrations to execute after an existing V1 history. With
`V8__build_printout_cache.sql`, however, six forward migrations (V3 through V8) were pending.
Flyway behaved correctly; the fixed test count was stale.

## Correction

The upgrade test now derives the expected count from `Flyway.info().pending()`, then performs a
second idempotent `migrate()` run and explicitly checks V1, V7, V8, and the V8 columns. The fresh-DB
integration path also checks V8 and the new printout-cache columns.

Build-printout coverage was extended with service-level cache reuse and invalidation plus a real
HTTP/PostgreSQL/filesystem lifecycle. This jointly verifies build creation, PNG storage, download,
identical reuse, build versioning, cache invalidation, and regeneration.

## API diagnostics

Every `/api/` response receives a server-generated `X-Request-Id`. Centrally logged `api_error`,
`security_401`, and `security_403` entries carry the same ID. Optional lifecycle logging is enabled
with `RBF_HTTP_LIFECYCLE_LOGGING=true` and contains only request ID, method, normalized route, status,
and duration. Payloads, query values, cookies, client IP, and user agent remain excluded. Integration
tests enable this diagnostic property explicitly; it is off by default in normal operation.

## JSON KISS/SOLID

Large hand-maintained JSON monoliths were split into responsibility-specific sources:

- OpenAPI: one operation or schema per file under `openapi/source/`; `openapi/openapi.json` is assembled deterministically.
- Build stats: one definition per file under `main/reference/build-stats/`.
- Build options and ships: one seed entry per file, grouped by category or rate; numeric prefixes preserve the existing catalog order.

A repository gate limits these hand-maintained JSON sources to 420 lines and prevents the removed
monoliths from returning. Data comparison against the starting repository confirmed identical build
stats (127), build options (230), and ships (67); OpenAPI is semantically identical except for the
release version jump from 1.0.13 → 1.1.0.

## Validation

Repository, documentation, security, Spring structure, controller/OpenAPI, SQL runtime, generator,
Java 21 syntax, infrastructure, update/artifact, TLS, Python/recovery, and frontend gates all succeeded.
The frontend suite reported 167 unit tests without errors and the production build succeeded.

The current execution environment contains no Maven 3.9 binary. Therefore `mvn verify` and the new
Testcontainers tests could not be started again here. The next CI/development machine with Maven must run
`mvn -f spring-api/pom.xml verify`; that run remains the authoritative Java/Spring/PostgreSQL verification.
