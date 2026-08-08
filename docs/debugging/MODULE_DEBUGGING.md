# Module-Oriented Debugging

This runbook describes a repeatable path from a visible failure to the responsible
module. The goal is a small, redacted evidence chain and a regression test at the
correct boundary. Module responsibilities are listed in the
[module catalog](../architecture/MODULE_CATALOG.md), and already-known production
causes in the [incident index](DEPLOYMENT_INCIDENTS.md).

## Diagnostic contract

A useful failure analysis answers, in this order:

1. Which public flow is affected (method, route template, user class, expected status)?
2. Does transport, authentication, authorization, business logic, persistence,
   integration, or presentation fail?
3. What is the smallest reproducible input that demonstrates the failure without
   secrets or personal data?
4. Which test will prevent exactly this cause in the future?

Diagnostic artifacts must not contain request/response payloads with user data,
cookies, CSRF/session tokens, webhook URLs, private keys, full IP addresses, or
unredacted database extracts.

## Local narrowing by layer

### API and backend

1. Determine the route and `operationId` in `openapi/source/operations/`; use
   `openapi/openapi.json` only as the assembled verification artifact.
2. Find the route directly in the module controller (`@*Mapping`) and compare the
   request DTO, `@PathVariable`/`@RequestParam`, and `@Valid @RequestBody` there with OpenAPI.
3. Trace from the controller to the service, policy, and repository/mapper boundary.
4. Classify the HTTP status: transport/bean binding 400, authentication 401,
   authorization/CSRF/origin 403, state conflict 409, business validation 422.
5. Add a service/policy test first; for security, SQL, or mapping, also add a real
   HTTP test against PostgreSQL.

```bash
rg -n 'operation_id|operationId|error text' openapi spring-api/src/main/java
rg -n 'api_error|security_401|security_403|api_request_complete' spring-api/src/main/java docs/debugging
mvn -f spring-api/pom.xml -Dtest='<TestClass>' test
```

Mock tests are insufficient when PostgreSQL types, constraints, transactions,
Spring Security, CSRF, cookie attributes, or generated API bindings are part of
the cause. The integration boundary for those cases lives under
`spring-api/src/test/java/eu/royalblackwater/api/integration/`.

### Database, seed, and retention

- Explain the schema only through the current Flyway history; do not alter existing
  migrations for debugging.
- For seed failures, inspect `seed_key`, stored checksum, and `is_seed_overridden`
  together. Repetition must remain idempotent.
- Normalize JDBC values at the persistence boundary; do not use test fixtures that
  silently replace PostgreSQL-specific types.
- Test retention with old, current, open, and closed rows. A deletion query must not
  include open data-subject requests.
- Before production data correction, establish the upgrade, backup, and recovery path;
  diagnostics alone do not authorize mutation.

### Frontend

1. Identify the failed request and HTTP status in browser tools without copying headers or cookies.
2. Trace route page → page composable → API/domain module.
3. Cover pure mapping/validation with a Node test, state transitions in the composable,
   and critical interaction with a Playwright smoke test.
4. Error states must remain visible and retryable; a failed save must not close a dialog
   or discard user input prematurely.

```bash
cd frontend
npm run test:unit
npm run test:browser -- --grep '<visible flow>'
```

Playwright mocks only `/api/` and proves UI behavior. Real cookie, session, CSRF,
role, and SQL boundaries belong in Spring integration tests.

### Infrastructure, deployment, and recovery

Collect from the origin system:

```bash
./infrastructure/scripts/diagnostics/debug.sh --area deployment --category errors --since 2h --tail 600
```

The collector uses `.env.origin.test` by default; production is selected explicitly
with `--production` and `.env.origin.production`. It bounds remote output and redacts
it locally. For failed activation, first preserve the `failed-*.log`, service state,
and Compose status. Only then may a focused, documented recovery action occur.
`docker compose down`, volume deletion, or changes to `shared/data` are not first-line
diagnostic steps.

## Failure class → evidence → regression test

| Failure class | Minimum evidence | Expected protection |
| --- | --- | --- |
| Transport/contract | method, route template, status, binding detail | generator and architecture check plus controller/HTTP test |
| Auth/permission | 401/403, boolean cookie/origin/CSRF indicators, role | security/policy test and protected HTTP route |
| SQL/persistence | query responsibility, SQL state/constraint, abstracted parameter form | service test plus PostgreSQL test |
| Seed/bootstrap | seed key/role code/status, repeat workflow | idempotent initializer/PostgreSQL test |
| Privacy | process type/status, no contents/identifiers | export, pseudonymization, and retention test |
| Frontend state | page, action, HTTP status, visible state | domain/composable test and browser smoke test where needed |
| External integration | target scope, event type, delivery status, bounded error | policy/renderer test; primary flow remains controlled |
| Deployment | release version, phase, readiness, redacted root cause | infrastructure/update/recovery contract test |

## Runbook: unexpected API 500

A generic `{"detail":"Internal server error."}` body is only the symptom. For a
500, always reproduce the real Spring/PostgreSQL path and trace the first server-side
root cause:

1. Reproduce the concrete HTTP call in a Spring Boot integration test against a
   PostgreSQL test container. Include method, path, status, and a bounded response
   excerpt in the assertion.
2. Use the `X-Request-Id` from the failed test response and find the corresponding
   `api_error status=500 request_id=...` line in Surefire/server output. Note the
   exception type and first application-owned stack frame; do not stop at the outer
   assertion failure.
3. Trace the route through OpenAPI/operationId → controller → service → repository/mapper.
   Investigate only the path that actually executed.
4. For Spring JDBC failures, inspect the **fully composed SQL meaning**: fragment
   boundaries, named parameters and bindings, and aliases/columns against Flyway.
   An error such as a merged parameter name often indicates missing whitespace between
   two Java SQL fragments.
5. Run `python3 infrastructure/scripts/quality/audit_sql_runtime.py` and inspect nearby
   query catalogs for the same failure class.
6. Keep the concrete endpoint as a permanent happy-path/regression test. For filter/sort
   SQL, also test the filtered query branch.
7. For review, admin, or other state machines, do not stop at an isolated request:
   create a real prerequisite, perform list/detail reads, execute the transition, and
   then read the new state again over HTTP. Test approve/reject or complete/reject
   separately. Repeating an already-consumed transition must return a controlled 4xx,
   never 500.
8. For mapper/reference resolution, treat optional foreign keys explicitly as nullable.
   In particular, never call `Map.get(RowValues.nullableLong(...))` directly: empty
   immutable maps from `Map.of()` do not accept a `null` key and can turn a normal
   pending/unreviewed state into a `NullPointerException` and thus a 500. Check for
   `null` first, then perform the lookup.
9. Then run `ApiSurfaceIntegrationTest` and finally `mvn verify`. The contract-wide
   no-5xx sweep, static SQL audit, and stateful lifecycle tests are three independent
   protections against different runtime failures.

Access Review reference:
`register -> pending -> status=all -> approve -> login -> approved`, and separately
`register -> pending -> reject -> rejected`. Sentinel IDs are acceptable for pure
transport tests; use real IDs/records for stateful regressions so repository, mapper,
and follow-up queries actually execute.

A 4xx may be functionally correct in the surface sweep; an unexpected 5xx never is.
For a new 500, fix the exception first rather than weakening the test.

Direct diagnostic commands:

```bash
grep -R -n -A100 -B20 'api_error status=500' spring-api/target/surefire-reports/
# For a concrete test failure, prefer searching for its X-Request-Id.
python3 infrastructure/scripts/quality/audit_sql_runtime.py
mvn -f spring-api/pom.xml -Dtest=ApiSurfaceIntegrationTest test
```

## Completing a debugging change

- Root cause fixed rather than the symptom.
- Success, failure, and permission paths tested.
- No additional sensitive logging introduced.
- Affected module row and permanently relevant runbook updated.
- Recurring, stable insight mirrored concisely into
  [`.agents/DEBUGGING_CACHE.md`](../../.agents/DEBUGGING_CACHE.md).
- `bash .agents/scripts/check-changes.sh --run` and, for a cross-cutting change,
  `make validate` succeeded.
