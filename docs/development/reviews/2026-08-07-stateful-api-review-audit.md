# Stateful API review audit — 2026-08-07

## Why this pass exists

The contract-wide no-5xx sweep is intentionally broad, but malformed bodies, missing
resources and sentinel path IDs can terminate a request before data-dependent service,
repository or mapper branches execute. Administration and review workflows therefore
need a second runtime layer that creates the prerequisite state and follows the complete
lifecycle through real HTTP requests against PostgreSQL.

## Required three-layer regression model

1. `ApiSurfaceIntegrationTest` walks the canonical 177-operation contract and rejects
   every unexpected 5xx, including optional GET query branches and media-type binding.
2. `audit_sql_runtime.py` independently checks statically resolvable SQL fragment
   boundaries, named parameters, tables and alias/column references against Flyway.
3. `ApplicationIntegrationTest` owns stateful lifecycle flows: create/submit, list/read,
   mutate/review, then read or authenticate again to prove the persisted result.

A green result in one layer never waives the other two.

## Registration Access Review reference flow

The registration workflow is the canonical review regression because it crosses public
registration, administrator review, user creation, optional Fleet membership, audit and
authentication. The positive branch is:

`register -> pending list -> status=all -> approve -> login -> approved list`

The negative-decision branch is:

`register -> pending list -> reject -> rejected list`

Both consumed transitions are repeated once and must return a bounded 4xx instead of
500. `status=all` is explicit in the API contract and frontend; an empty query value must
not fall back to the endpoint's `pending` default.

## Additional stateful administration coverage

The same integration boundary now round-trips moderator/user administration, Build-role
CRUD, privacy request/contact review and IP block/unblock. The API surface test also
uses real seed or created IDs for safe read-only resource parameters so more GET
operations reach repository and mapper code rather than stopping at synthetic 404s.

## Rule for future fixes

When an admin/review UI reports an internal server error, reproduce the exact lifecycle
with real prerequisite data, extract the first server-side `api_error status=500` root
cause, fix that cause, and retain the lifecycle as a permanent regression. Do not weaken
the no-5xx assertion or replace stateful coverage with a sentinel-ID transport probe.

## Follow-up: pending reference nullability

The first full runtime execution of the review lifecycle exposed a mapper-boundary bug
in the pending list state. Pending requests legitimately have neither `created_user_id`
nor `reviewed_by_id`. `UserDirectoryService.readMany([])` returns an immutable empty
`Map.of()`, and the registration mapper path then performed `userMap.get(null)`. Java's
immutable map rejects that null lookup, so a valid pending request became an HTTP 500.

The service now null-guards optional user references before lookup. A focused unit test
keeps the pending/null-reference state covered, the contract-wide surface test keeps the
real HTTP endpoint covered, and `audit_spring_backend.py` rejects direct
`Map.get(RowValues.nullableLong(...))` patterns so the same class of bug cannot silently
return elsewhere. The lifecycle fixture helper also selects `fleet_id` explicitly; tests
must not infer a field that their SQL fixture query did not select.
