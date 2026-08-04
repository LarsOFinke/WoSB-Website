# Testing

Run the complete gate with:

```bash
make validate
```

It includes:

1. Spring unit and integration tests with PostgreSQL Testcontainers.
2. Flyway empty-database and supported-upgrade tests.
3. Spring Security, session, CSRF and authorization tests.
4. API operation coverage for all 177 contract operations.
5. MapStruct compilation with unmapped targets as errors.
6. Build-calculation golden cases.
7. Query batching/N+1 invariants and list-filter tests.
8. Vue unit, locale, binding, responsive and production-build checks.
9. Release artifact inventory, tamper and safe-extraction tests.
10. Backup-set and recovery-bundle contract tests.
11. Shell syntax, Compose, container and repository hygiene checks.

A release is not production-ready when Maven, frontend build, PostgreSQL integration tests or container builds were skipped. Local quick mode may skip unavailable toolchains, but CI may not.
