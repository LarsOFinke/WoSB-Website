# Cached Quick Overview – Debugging

This cache points quickly to the smallest safe evidence. Detailed guides live under
[docs/debugging](../docs/debugging/README.md); known production causes are indexed in
[Deployment Incidents](../docs/debugging/DEPLOYMENT_INCIDENTS.md). Do not copy raw logs,
cookies, tokens, personal data, or full IP addresses into the working context.

## Route by symptom

| Symptom | Check first | Then |
| --- | --- | --- |
| API 500 | central `api_error` line, method/path/exception type | route → operationId → module controller → service → repository/mapper |
| 401 | `security_401`, session cookie only as present/not present | `SessionAuthenticationFilter`, active user, and role fetch |
| 403 | `security_403`, origin/CSRF indicators | authority, domain policy, CSRF, and host/origin separately |
| 400/422 | contract schema and `ApiExceptionHandler` | distinguish transport binding (400) from business rejection (422) |
| empty/wrong API response | contract mapper and internal DB columns | do not hide unknown fields by loosening the contract |
| startup failure | property binding, Flyway, Hibernate `validate` | readiness and first root-cause stack trace |
| seed/master data | seed key, checksum, override flag | rerun seeder idempotently; do not edit a migration |
| legacy partial restore/migration | dry run + first preflight exception | verify semantic FK resolution; never restore old IDs or complete Python dumps into the Java DB |
| fleet/squad | fleet ID, membership status, role code/capabilities | bootstrap repair and AccessPolicy/HTTP test |
| privacy/cookie | policy version, decision present, no key values | retention, export exclusions, protected route after deletion |
| strategy planner | SVG screen matrix, overlay JSON keys, referenced IDs | ship/build compatibility, ownership, publication state |
| frontend does not load | browser console, failed API status, route | page → composable → API/domain; Vite build and browser smoke test |
| deployment/update | locally redacted diagnostics, failed activation log | artifact version, Compose, readiness, rollback; never delete data |

## Token-efficient local workflow

```bash
bash .agents/scripts/project-context.sh
rg -n "<operationId|error text|class>" spring-api frontend contracts
bash .agents/scripts/check-changes.sh
```

Then run only the focused test. On failure, the agent gates provide the last 200 lines;
request full output only when necessary with `AGENT_GATE_VERBOSE=1`. Reuse long-running
sessions; do not start the same test again in parallel.

## Production diagnostics

```bash
./infrastructure/scripts/diagnostics/debug.sh --area api --category http-500 --since 30m --tail 400
./infrastructure/scripts/diagnostics/debug.sh --area security --category auth --since 30m --tail 400
./infrastructure/scripts/diagnostics/debug.sh --area deployment --category errors --since 2h --tail 600
```

Valid areas: `overview`, `staff`, `calendar`, `api`, `security`, `gateway`, `database`,
`deployment`, `all`. Categories: `errors`, `warnings`, `http-500`, `auth`, `migration`,
`all`. Collect narrowly first, then widen the time range or area if needed. The collector
reads `.env.origin.test` by default; production requires `--production` and
`.env.origin.production`. It writes nothing remotely and stores only locally redacted
output under `.diagnostics/`.

## Known stable pitfalls

- `/api/auth/me` is public and returns `200 null` for a missing/invalid session; verify
  session revocation on a protected route.
- Bean Validation and JSON/query binding return HTTP 400 centrally; business-domain
  validation may return 422.
- Handle multipart endpoints separately: the OpenAPI media type and generated `consumes`
  must match. A missing/broken multipart body is 400, wrong Content-Type is 415, and a
  size limit is 413; none of these transport errors may become 500 through the generic handler.
- Cookie settings open automatically without a saved decision; initialization failures keep
  the settings controls visible in a fail-closed state. Consent reads are cache-sensitive because
  the decision is keyed by a cookie: the frontend and backend enforce `no-store`. For a missing
  banner, inspect browser `[privacy] cookie_consent_initialize_complete` (`hasDecision`,
  `visible`) and correlate the request ID with `privacy_cookie_consent_state`; never log or copy
  the consent key.
- For API 500s, correlate the response `X-Request-Id` with
  `api_error status=500 request_id=...` in Surefire/server output and read the first
  application-owned stack frame. The generic response body is not the root cause. Enable
  successful lifecycle logs only when needed with `RBF_HTTP_LIFECYCLE_LOGGING=true`; do not
  log payload/query/IP data.
- Composed JDBC SQL can fail only at runtime even when Java is valid: check fragment boundaries,
  named parameters/bindings, and aliases/columns with
  `python3 infrastructure/scripts/quality/audit_sql_runtime.py`; then run the affected HTTP
  path plus `ApiSurfaceIntegrationTest`.
- A green surface sweep does not replace a stateful test for review/admin flows. Reference:
  create prerequisite -> pending/list/read -> approve/reject/resolve -> follow-up read/login/audit.
  Repeat an already-consumed transition and require a controlled 4xx. Use real IDs rather than
  404 sentinel values for these flows.
- Registration Access Review must cover both branches: `status=all`, Approve followed by
  login/Approved-Read, and Reject followed by Rejected-Read.
- Never use optional DB references directly as `Map.get(nullableLong(...))`. A pending/unreviewed
  record yields `null` there; in particular, `Map.of()` throws an NPE when looked up with `null`
  and masks a valid state as an API 500.
- JDBC can return `DATE` as `java.sql.Date`; normalize it at the `RowValues` boundary.
- Remove internal seed/relation fields before strict contract conversion.
- JSON documents embedded inside string-valued API fields still use the application `ObjectMapper`
  and therefore inherit global `SNAKE_CASE`. If their internal browser contract is camelCase,
  pin every multiword record component with `@JsonProperty`, retain snake-case aliases for stored
  legacy documents, and test with the production naming strategy rather than `new ObjectMapper()`.
- Strategy pointer coordinates cannot be derived from the SVG element's bounding rectangle when
  `preserveAspectRatio` introduces letterboxing or CSS scales the canvas. Transform `clientX/Y`
  through the inverse `getScreenCTM()` into viewBox coordinates and retain a bounded fallback for
  detached SVGs; cover non-uniform screen matrices in a regression test.
- A valid strategy build reference is a pair, not two independent existing IDs: query each selected
  build's `ship_id` and require it to equal the marker's numeric `shipId`. Filter the editor choices
  by the same relation, but retain the server check because overlay JSON is an untrusted boundary.
- Never fix generated controllers or contracts directly; change the generator source and run `--check`.
- Flyway upgrade regressions must not hard-code the number of future migrations. Before upgrading,
  use `Flyway.info().pending()` as the expected count; afterward run `migrate()` a second time with
  `0` changes and explicitly verify that functionally important versions/columns were applied exactly
  once. Fresh DB and V1 upgrade remain separate test paths.
- Treat legacy build data as a logical migration: use the exact same reviewed SQL file first in tests
  as dry-run -> commit -> UI/API verification, then in production as dry-run -> commit. Resolve
  ships/options/roles/features semantically; never import historical numeric IDs, user/auth data, or
  master data from the complete Python dump. Runbook: `docs/debugging/LEGACY_BUILD_DATA_MIGRATION.md`.
- Production data, volumes, `shared/data`, and active releases are never valid debug cleanup targets.
- When Maven reports stale source lines or impossible old test behavior, trust the absolute path it
  prints for `target`/Surefire reports. Verify `pwd -P` and `realpath pom.xml`; a shell can remain
  inside a directory that was later moved to Trash, and `mvn clean` only cleans that physical tree.
- Generic coverage/surface harness failures are actionable only after synthetic objects are internally
  valid. Constructor validation should trigger a second type-correct construction attempt rather than
  a partial Mockito object with null internals. Mockito stubs/verifications must use matchers for all
  arguments once any matcher is used.

## Cache maintenance

Add a new recurring cause here only after reproducing the failure, fixing the root cause, and adding
a regression test; detailed rationale belongs in a runbook. Then run
`bash .agents/scripts/check-cache.sh` and `bash .agents/scripts/check-docs.sh`.

### Build print/image preparation
- Build print preparation may embed dozens of master-data images from `/api/files/<id>/content`.
- These media reads must not consume the interactive `api_general` NGINX rate budget. They use the dedicated bounded `file_content` zone.
- The frontend embedding path must retain HTTP caching and bounded concurrency (currently 6); do not restore `cache: 'no-store'` or unbounded `Promise.all()` fetching for image resources.
- Symptom pattern: one prepare succeeds, later prepares fail, browser cache clearing does not help, gateway/server restart temporarily helps. Check gateway access logs for file-content HTTP 429/503 before changing application caches.
- Preserve the global API limiter; fix media routing/embedding behavior rather than weakening general anti-abuse controls.

### Build printout cache (since v1.0.13)

Build PNGs are a server-wide **derived cache**. Never begin diagnosis by treating it as a
user/browser cache. The client forms the key `print-v<version>:<sha256>` from the renderer
version plus the SVG actually rendered and may use a server hit only when
`printout_cache_key` and `printout_source_updated_at == updated_at` match the freshly loaded
build. The URL carries the `cache_key` so the HTTP cache cannot reuse an old revision under
an unchanged URL.

Invariants:

- Saving to the cache must never change `builds.updated_at`.
- PUT locks the build row (`FOR UPDATE`), checks the source revision, and permits cache population
  only by owner/staff.
- PNG files are checksum-versioned; the DB commit selects the valid file. Rollback deletes the new
  file; commit deletes the previous file.
- Build update/role change invalidates metadata and file after commit; build deletion removes all
  associated printout files after commit.
- Global quota and `UPLOAD_MINIMUM_FREE_MB` also apply to printouts.
- Scheduled cleanup removes stale DB metadata, orphans, old stable `build-<id>.png` files, and
  `.upload` fragments; fresh orphan candidates receive a one-hour grace window to avoid racing
  active cache commits.
- Layout, semantics, or any other rendering change must bump `BUILD_PRINT_RENDERER_VERSION`.
  Identical cache keys must never produce different PNG content; the server otherwise returns 409.

For the symptom `Prepare succeeds once, then fails`, check separately first: media rate limit
(429/503, v1.0.12) versus cache lifecycle (404/409/quota). A container restart is not a cache
cleanup strategy.
