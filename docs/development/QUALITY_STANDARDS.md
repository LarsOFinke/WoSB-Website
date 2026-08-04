# Quality standards

This document is the binding technical quality contract for the repository.
`AGENTS.md` defines the working rules; architecture, security, database, CSS and
operations documents refine this standard for their respective scope. The
`.agents/` material accelerates navigation but never overrides a primary source.

## Quality characteristics

| Characteristic | Required outcome | Primary evidence |
| --- | --- | --- |
| Functional correctness | Contract, implementation, validation and error semantics agree | domain tests, integration tests, generated-contract audit |
| Security and privacy | Server-side authorization, least privilege, bounded data collection and secret-safe diagnostics | Spring Security tests, security audit, privacy workflows |
| Maintainability | Named responsibilities, clear dependency direction and small cohesive files | repository audit, architecture boundaries, review |
| Performance efficiency | Bounded queries and payloads; no N+1 or unbounded list work | query-count tests, list-filter tests, Spring audit |
| Reliability and recoverability | Failure is explicit; releases, schema and data can be restored coherently | artifact, backup, migration, rollback and recovery tests |
| Operability | Idempotent automation, actionable diagnostics and predictable host layout | infrastructure tests, smoke tests, operations documentation |
| Accessibility and responsive UX | Keyboard, focus, contrast, touch and supported viewport behavior remain usable | frontend tests, CSS audit and manual release review |
| Reproducibility | Locked dependencies and checksummed source-free artifacts produce the same release inputs | lockfiles, CI build, manifest and tamper checks |

Correctness, security, privacy and data preservation take precedence over
convenience or cosmetic consistency. A green UI guard never substitutes for a
server-side permission check; a successful application start never substitutes
for a verified backup and recovery path.

## Architecture and maintainability

- Follow the dependency directions in `docs/architecture/ARCHITECTURE.md` and
  `frontend/ARCHITECTURE.md`; transport layers orchestrate and domain services own
  business rules.
- Inject dependencies through constructors. Do not introduce field injection,
  service locators or generic manager/wrapper layers without a concrete lifecycle
  or substitution benefit.
- Prefer the smallest complete change and existing abstractions. Fix root causes;
  do not hide failures through broad exception handling, permissive fallbacks or
  duplicated compatibility paths.
- A source file has one nameable main responsibility. Executable Java and
  JavaScript responsibilities should be split around 300–400 lines and must stay
  within enforced repository limits. Cohesive declarative catalogs are reviewed
  separately but must not accumulate unrelated logic.
- Generated sources and build outputs are changed through their generator, not by
  hand. Local environments, caches, runtime data and release outputs stay
  unversioned.

## Backend correctness and security

- Java 21, constructor injection and explicit domain boundaries are mandatory.
- `contracts/api-contract.json` is the HTTP contract. Generated controllers bind
  and validate transport data, then delegate each operation to exactly one
  operation handler.
- Typed validated contracts and MapStruct use fail-closed mappings; unmapped
  target fields are compilation errors.
- Spring Security is the sole authentication and authorization boundary. Mutating
  browser requests retain session/JWT validation as applicable, CSRF, host and
  origin controls. Endpoint-local authentication shortcuts are prohibited.
- Transactions encompass a business mutation and its required audit record.
- SQL remains parameterized. User-controlled identifiers, sort clauses or SQL
  fragments require an explicit allow-listed mapping.
- `open-in-view=false`: response assembly must not depend on lazy loading outside
  the transaction. Authentication queries fetch every authority needed by the
  security filter before the persistence context closes.
- Expected client errors return bounded, actionable 4xx responses. Unexpected
  faults use centralized `api_error` diagnostics without payloads, secrets,
  tokens, full IP addresses or personal content.

## Filters and query efficiency

- Growing list endpoints expose bounded search/pagination and explicit domain
  filters. Default and maximum limits are enforced before numeric narrowing.
- Filtering is pushed into indexed database queries where practical; do not load
  complete tables for application-side filtering.
- Collections are fetched in batches or projections, never inside a result loop.
  Avoid multiple bag fetches and eager collections.
- Query-count tests cover critical list/detail assemblers;
  `scripts/audit_spring_backend.py` enforces static invariants.
- New sort/filter paths include matching indexes or a documented reason why the
  existing access path is sufficient.

## Frontend and design quality

- Pages compose; composables own state/lifecycle/workflows; API modules own
  transport; domain modules own deterministic rules; reusable presentation lives
  in components.
- Frontend guards are user experience only. Protected data and actions remain
  server-authorized.
- Loading, empty, error and success states must be explicit and accessible.
  Errors do not silently reveal internal implementation details.
- Keyboard navigation, visible focus, semantic controls, reduced motion, touch
  targets, translations and supported viewport widths are part of correctness.
- CSS follows `docs/reference/CSS_ARCHITECTURE.md`: use tokens, the narrowest
  owning layer, low specificity and feature-local styles. Do not append unrelated
  overrides to the end of the cascade.

## Data, migrations and privacy

- PostgreSQL is the only production database. Flyway is the only schema owner;
  released migrations are immutable and Hibernate remains on `ddl-auto=validate`.
- Entity, migration, index, supported upgrade and recovery path change together.
  Prefer additive expand/contract migrations and preserve administrative data.
- New personal data requires a documented purpose and legal/operational basis,
  retention, access/export, correction and deletion path.
- Logs, fixtures, webhooks and errors contain no secrets, tokens, personal
  content, complete IP addresses or unnecessary identifiers.
- Webhooks are sparse audit/action signals. Delivery must not block the primary
  transaction without a documented product requirement.

## Operations and recoverability

- Production deploys compiled, checksummed, source-free artifacts only.
- Database migration, coordinated backup, release switch, readiness and rollback
  form one controlled workflow. Normal updates never bypass the backup gate.
- Restore is staged, version-aware and fail-closed. Application artifact, Flyway
  schema and persistent files are restored coherently.
- Runtime containers remain read-only where supported, capability-dropped and
  protected with `no-new-privileges`; secrets are mounted or injected, not baked
  into images.
- Infrastructure scripts are idempotent orchestrators around focused helpers.
  Critical file changes are atomic where practical and failures have a non-zero
  exit code plus an actionable message.
- The API never gains direct host root privileges. Privileged actions cross the
  documented owner-only request boundary to root-owned systemd runners.

## Documentation and agent assistance

- Behavior, configuration, migration and operations documentation change in the
  same commit as the implementation.
- `docs/README.md` is the human documentation index. `AGENTS.md` points agents to
  `.agents/ONBOARDING.md`, which in turn references `.agents/PROJECT_CACHE.md` and
  live helper scripts.
- Agent caches contain stable navigation and verified debugging conclusions, not
  secrets or volatile counts. Runtime topology, primary entry points, gates and
  known incident resolutions are updated when they change.
- Time-bound audits remain evidence, not mutable architecture specifications.
  Current behavior belongs in architecture, development, reference or deployment
  documentation.

## Verification strategy

Run focused tests while developing, then the gates selected for the changed
scope. `bash .agents/scripts/check-changes.sh` can recommend existing gates; it
does not waive them. Cross-cutting and release-affecting changes require:

```bash
make validate
```

At minimum, directly affected tests/linters and
`python3 scripts/check_repository.py --strict-tree` must pass. A skipped toolchain,
container build or integration suite is not a successful release result. Report
environmental blockers separately from product failures and rerun the missing
gate in a supported environment.

## Definition of done

A change is complete only when:

1. contract, implementation, configuration and documentation agree;
2. authorization, privacy, migration and recovery consequences were checked;
3. success, validation/error and permission behavior have proportional tests;
4. performance remains bounded for growing data sets;
5. focused checks and required repository gates pass without hidden skips;
6. generated/runtime artifacts and unrelated user changes remain untouched;
7. operational changes provide an actionable failure and rollback path.

An exception to a hard standard requires a narrow documented scope, reason,
risk, owner and removal condition. Existing exceptions are not precedent for
expanding them.
