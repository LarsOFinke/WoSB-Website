# API runtime 500 audit — 2026-08-07

## Scope

The review followed the Fleet-management failure pattern across the complete Spring
API: reproduce through HTTP, identify the first server-side exception, trace the
executed service/repository path, inspect assembled SQL, and then preserve the case
as a regression. The review also added a second independent layer that sweeps the
OpenAPI surface for unexpected 5xx responses.

## Static persistence review

`infrastructure/scripts/quality/audit_sql_runtime.py` now checks SQL failure classes
that Java compilation cannot detect:

- token boundaries when query constants and optional fragments are concatenated;
- statically resolvable named SQL parameters versus supplied bindings;
- statically resolvable `alias.column` references versus the Flyway schema;
- compatibility-schema table/column drift versus the current modular schema.

At the time of this review the audit covers 61 schema tables, 1,067 statically
resolvable table-reference checks, 1,371 alias/column-reference checks, 287 statically
resolvable parameterized JDBC calls and all 5 current `SqlUpdate` table/column
schemas. Dedicated quality tests also prove that the audit rejects the original merged-parameter pattern, retired tables and invalid alias/column references. The expanded table check exposed one
additional real stale-schema defect: master-data option deletion still referenced
three retired Build relation tables. The delete guard now uses the normalized
`build_slots` relation plus `ship_upgrade_effect_overrides`. No additional definite
defect of these checked classes remained after that repair. Runtime-only query construction and mapper behavior therefore remain covered by
PostgreSQL integration tests rather than being assumed safe.

## Runtime regression expansion

`ApiSurfaceIntegrationTest` derives its cases from the canonical OpenAPI document.
All 177 operations remain inventoried. The 70 GET operations execute against the
real Spring application and PostgreSQL, and GETs with optional query parameters run
a second filtered variant so dynamic query branches are entered. The 107 non-GET
operations receive a non-destructive transport/error-boundary smoke. Any 5xx fails
the suite.

`ApplicationIntegrationTest` retains deeper domain assertions and now also performs
create/read round trips for Builds, Forum threads, Guides and Groups in addition to
its existing Fleet/Squad, Calendar, auth/security and administration coverage.
These tests are intentionally complementary: the surface sweep finds broad runtime
regressions while explicit domain round trips prove important persistence paths with
successful data.

### Multipart transport regression

The first full write-surface run exposed a transport-only failure class: the two
`multipart/form-data` operations (`PUT /api/builds/{build_id}/printout` and
`POST /api/files`) were probed with malformed JSON and Spring's multipart binding
exceptions fell through the generic exception handler as HTTP 500. Generated route
interfaces now declare the contract media type explicitly, the global exception
boundary preserves framework-originated 4xx statuses instead of reclassifying them
as 500, and malformed multipart requests have a dedicated 400 path. Upload-size
rejections remain 413.

The API surface suite now chooses its probe transport from OpenAPI: JSON bodies are
probed as JSON, multipart bodies as multipart. It additionally sends JSON to every
multipart operation and requires HTTP 415. This distinction is mandatory when
triaging a surface-suite failure: first decide whether the request reached domain
code or failed at MVC content negotiation/request-part binding.

## Required response to a new 500

Do not change an expected status to tolerate an unexpected 5xx. Capture the first
`api_error status=500`, use the exception type and first project stack frame to find
the executed path, run the SQL runtime audit when persistence is involved, repair
the root cause, and retain a focused endpoint regression. Then rerun the API surface
suite and the full Maven verification gate.

The durable procedure is documented in `docs/debugging/MODULE_DEBUGGING.md`,
`docs/development/TESTING.md`, `docs/development/QUALITY_STANDARDS.md` and
`.agents/DEBUGGING_CACHE.md`.
