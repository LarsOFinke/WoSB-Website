# Spring Boot Migration Completion Review

Date: 2026-08-04

## Result

The application runtime is Spring Boot only. The former Python/FastAPI backend, catch-all proxy,
Alembic runtime and Python seeding path have been removed. The frozen HTTP contract contains 177
unique operations and every operation is owned by exactly one native Spring handler.

## Runtime architecture

- Java 21 and Spring Boot provide the complete HTTP API.
- Spring Security owns authentication, CSRF, request-boundary checks and administrator routing.
- Flyway owns schema creation and every forward migration.
- A reviewed one-time adoption gate fingerprints the final legacy schema before creating Flyway
  history for an existing installation. Normal startup never enables broad automatic baselining.
- MapStruct and generated Java records provide typed transport boundaries.
- PostgreSQL is the only application database.
- Reference and system data are synchronized from versioned Spring resources.

## Deployment and recovery

CI compiles the executable JAR and frontend distribution. Production receives one checksummed,
immutable release artifact. The target host builds only minimal runtime images from those compiled
artifacts and activates a versioned release atomically. Production deployment does not pull source
code or execute Maven, npm or Python application builds.

Backup sets contain a PostgreSQL custom dump, persistent runtime files, release identity and a
checksummed manifest. Restore validation imports into an isolated database, runs Flyway validation
and forward migrations, starts the Spring application and performs readiness checks before an
activation can occur.

## Filter boundaries

Shared list filters normalize search text, enforce maximum lengths, reject fractional or overflowing
numeric values and bound limits and offsets. They are used for high-volume build, ship, squad and
user queries. Forum and guide search/category inputs are length-bounded, and their result sets have
hard server-side caps where the frozen public contract does not expose pagination.

## N+1 review

The following formerly proportional read paths are batched or aggregated:

- squad members and squad permissions,
- newcomer-guide resources,
- ship weapon summaries,
- master-data ship mounts, mortar data and upgrade overrides,
- guide owner references,
- guide build references,
- build classifications and slots.

Build list/detail assembly also shares a request-local runtime catalog so repeated ship, feature and
option lookups occur once per distinct catalog key rather than once per result row. Static repository
invariants and focused query-count tests protect these paths.

Mutation loops that write child collections are intentionally retained. They are bounded by request
validation and execute inside the parent transaction; they are not N+1 read paths.

## Validation gates

The repository requires:

- exact native ownership of all 177 API operations,
- absence of the Python backend and legacy runtime services,
- Java source parsing with a Java 21 compiler,
- Maven verification with MapStruct fail-on-unmapped targets,
- Testcontainers startup against PostgreSQL with Flyway, reference seeding and bootstrap admin,
- frontend unit, binding and production-build checks,
- infrastructure, update, recovery, security and strict-tree audits,
- artifact verification and runtime image builds in CI.

The local completion run executed every gate available in the isolated workspace. Maven dependency
resolution, the complete npm production build and Docker/Testcontainers execution remain CI gates
because this workspace has no Maven installation, Docker daemon or external package-network access.
