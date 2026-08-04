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
```

The frontend gate requires the Playwright Chromium runtime. Install it once with
`npx playwright install chromium` from `frontend/`; CI installs Chromium and its
system dependencies explicitly before running the gate.

The helpers do not implement separate assertions. They delegate to `make`, the
existing test scripts and the strict repository checker. A failed or skipped
check remains failed/skipped even when the cause is a local sandbox or missing
toolchain; record the limitation and rerun it in a supported environment.

For frontend changes, test logic, page bindings, locales, responsive invariants
and a production build. Backend changes require Maven compilation/tests and, when
persistence is involved, PostgreSQL/Testcontainers. Infrastructure changes require
the infrastructure/update contract suites; backup, migration or recovery changes
also require the recovery tests.
