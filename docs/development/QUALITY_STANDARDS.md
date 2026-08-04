# Quality standards

## Backend

- Java 21, constructor injection and clear domain boundaries.
- Typed validated contracts; MapStruct fails on unmapped target fields.
- Central Spring Security; no endpoint-local authentication shortcuts.
- Transactions encompass business mutation and its required audit record.
- Parameterized SQL only; no user-controlled identifiers or clauses.
- Java files stay below 420 lines.

## Filters and query efficiency

- Growing list endpoints expose bounded search/pagination and explicit domain filters.
- Default and maximum limits are enforced before numeric narrowing.
- Collections are fetched in batches or projections, never inside a result loop.
- Avoid multiple bag fetches and eager collections.
- Query-count tests cover the largest list and detail assemblers; `scripts/audit_spring_backend.py` enforces static invariants.

## Operations

- Production deploys compiled, checksummed artifacts only.
- Database migrations, release switch, backup and readiness form one controlled workflow.
- Restore is staged and fail-closed.
- Runtime containers are read-only, capability-dropped and protected with `no-new-privileges`.
