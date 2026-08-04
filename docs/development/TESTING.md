# Testing

Run the complete gate with:

```bash
make validate
```

It includes:

1. Spring unit and integration tests with PostgreSQL Testcontainers.
2. Flyway empty-database and supported-upgrade tests.
3. Spring Security, session, CSRF and authorization tests.
4. API operation coverage for every currently generated contract operation.
5. MapStruct compilation with unmapped targets as errors.
6. Build-calculation golden cases.
7. Query batching/N+1 invariants and list-filter tests.
8. Vue unit, locale, binding, responsive, production-build and Chromium browser
   smoke checks for navigation, accessibility and critical forms.
9. Release artifact inventory, tamper and safe-extraction tests.
10. Backup-set and recovery-bundle contract tests.
11. Shell syntax, Compose, container and repository hygiene checks.

A release is not production-ready when Maven, frontend build, PostgreSQL integration tests or container builds were skipped. Local quick mode may skip unavailable toolchains, but CI may not.

## Scope-based development checks

Use focused feedback during implementation, then run the required release gate:

```bash
bash .agents/scripts/check-changes.sh         # show checks for the current diff
bash .agents/scripts/check-changes.sh --run   # run those existing gates
bash .agents/scripts/check-frontend.sh        # frontend tests/build with temporary env
bash .agents/scripts/check-docs.sh            # documentation references and repository checks
bash .agents/scripts/check-all.sh             # quiet wrapper around the full release gate
```

The frontend gate requires the Playwright Chromium runtime. Install it once with
`npx playwright install chromium` from `frontend/`; CI installs Chromium and its
system dependencies explicitly before running the gate.

Agent wrappers suppress successful tool chatter to conserve context and print a
bounded failure tail. Set `AGENT_GATE_VERBOSE=1` only when the complete underlying
output is needed for diagnosis.

`ApplicationIntegrationTest` starts the complete Spring application against a
PostgreSQL Testcontainer and exercises real HTTP behavior for public health and
registration, sessions, administrator authorization, CSRF, origin checks and
bounded error responses. Run it in isolation with:

```bash
mvn -f spring-api/pom.xml -Dtest=ApplicationIntegrationTest test
```

Mockito is loaded as an explicit JVM startup agent. Maven resolves the agent path
through `maven-dependency-plugin`, so default and overridden local repositories
use the same configuration and tests never rely on dynamic self-attachment.

The Playwright suite starts Vite and replaces only `/api/` requests with
deterministic browser fixtures. It verifies browser-side navigation and form
contracts without weakening the Spring integration boundary. Run it with:

```bash
cd frontend
npm run test:browser
```

The helpers do not implement separate assertions. They delegate to `make`, the
existing test scripts and the strict repository checker. A failed or skipped
check remains failed/skipped even when the cause is a local sandbox or missing
toolchain; record the limitation and rerun it in a supported environment.

For frontend changes, test logic, page bindings, locales, responsive invariants,
critical browser flows and a production build. Backend changes require Maven
compilation/tests and, when persistence is involved, PostgreSQL/Testcontainers.
Infrastructure changes require the infrastructure/update contract suites; backup,
migration or recovery changes also require the recovery tests.
