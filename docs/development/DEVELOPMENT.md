# Development

## Quick orientation for repository agents

`AGENTS.md` is the binding working guide. Agents then start with
[`.agents/ONBOARDING.md`](../../.agents/ONBOARDING.md) and a current snapshot
without secrets:

```bash
bash .agents/scripts/project-context.sh
```

The project cache accelerates navigation but does not replace this development
documentation or the affected source, test, and configuration files.

## Backend

Requirements are Java 21, Maven 3.9+, and PostgreSQL. Docker with Testcontainers
is required for the complete integration test suite.

```bash
mvn -f spring-api/pom.xml spring-boot:run
```

Local configuration is supplied through the environment variables documented in
`application.yml`. PostgreSQL is the only supported database. Flyway migrates the
schema; Hibernate validates it with `ddl-auto=validate`.

Backend changes follow the current module boundary:

```text
OpenAPI -> generated API DTO -> Controller -> Service -> Repository
                                  |            |
                                  |            +-> PostgreSQL
                                  +-> Mapper <-> DTO/Entity/Row
```

Controllers own the Spring MVC routes, remain HTTP-oriented, and validate typed DTOs
directly. Services own business logic, authorization, and transactions, but neither SQL
nor raw HTTP/DB representations. Repositories own persistence and query catalogs; mappers
own representation changes. Domain-internal transfer objects live in `dto`, persistence
state in `entity`; generic `model` packages are not permitted. New or moved Java types
must be committed with explicit, resolvable, and used imports.

## Frontend

```bash
cd frontend
cp .env.example .env
npm ci
npx playwright install chromium
npm run dev
```

Node 22 matches CI. Playwright Chromium is installed locally once; CI installs the browser
and system dependencies before the complete gate. The lockfile must contain only public
registry URLs.

## Commands

```bash
make test       # repository, security, Java, frontend, and infrastructure checks in fast mode
make test-full  # complete Spring, PostgreSQL, frontend, and recovery validation
make validate   # complete release gate
make clean      # remove generated files and build output
make clean-all  # additionally remove local dependency environments
make check-tree # verify a clean repository tree without packaged artifacts
```

For focused feedback, these entry points are especially useful:

```bash
mvn -f spring-api/pom.xml -Dtest=ApplicationIntegrationTest test
cd frontend && npm run test:browser
```

For an existing diff, `bash .agents/scripts/check-changes.sh` can show the smallest
appropriate check set. Cross-cutting changes always remain a case for `make validate`.

New API features need permission, success, and failure cases. Growing lists require
bounded pagination, search, and domain filters. Collections are loaded in batches or
through projections; query-count tests protect critical assemblers from N+1 regressions.

## Dependencies

Backend dependencies are maintained exclusively in `spring-api/pom.xml`. MapStruct must
fail on unmapped target fields. Frontend dependencies are installed reproducibly through
`frontend/package-lock.json`.
