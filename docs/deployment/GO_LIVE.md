# Go-live checklist

- `VERSION`, Maven, frontend metadata and the OpenAPI contract carry the same release version.
- `mvn clean verify` is green from `spring-api/` for the exact release tree, including Surefire, packaging and all JaCoCo checks.
- `make validate` and full CI are green for the exact release commit; no required toolchain/integration/container stage was skipped.
- `git status --short` was reviewed before commit; local `patches/*.patch` payloads are not tracked or staged.
- Deployment artifact checksum and provenance are stored.
- Staging installed the same artifact and passed smoke tests.
- Flyway builds an empty database and upgrades the supported predecessor snapshot.
- Security, authorization and CSRF tests pass.
- Critical lists have bounded filters and verified query counts.
- TLS, DNS, firewall and forwarded-header configuration are independently checked.
- Bootstrap credentials are rotated or removed.
- Legal notice, privacy text and retention settings are approved.
- A coordinated backup set and encrypted recovery bundle exist.
- A separate-host restore exercise reaches Spring readiness and HTTPS smoke success.
- Rollback metadata points to an available previous release and database backup.
