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
  `frontend/ARCHITECTURE.md`; module controllers own HTTP routing and bind/validate
  generated API DTOs directly, services own business rules and transactions,
  repositories own persistence access, module-local `repository/queries` catalogs
  own SQL definitions, and mappers own representation changes.
- Inject dependencies through constructors. Do not introduce field injection,
  service locators or generic manager/wrapper layers without a concrete lifecycle
  or substitution benefit.
- Prefer the smallest complete change and existing abstractions. Fix root causes;
  do not hide failures through broad exception handling, permissive fallbacks or
  duplicated compatibility paths.
- A source file has one nameable main responsibility. Executable Java and
  JavaScript responsibilities should be split around 300–400 lines and must stay
  within the enforced 420-line repository limit. The locale message modules and
  `autoLocalizationCatalog.js` are explicit declarative exceptions; they are
  reviewed separately and must not accumulate executable or unrelated logic.
- Generated sources and build outputs are changed through their generator, not by
  hand. Local environments, caches, runtime data and release outputs stay
  unversioned.

## Persistence runtime correctness

A JDBC statement is not considered verified merely because Java compiles. SQL that
is assembled from constants, optional filters or allowlisted sort fragments must be
validated at both the static and PostgreSQL runtime boundaries. In particular:

- adjacent SQL fragments must preserve an explicit token boundary; never rely on
  Java source indentation or text-block appearance to provide runtime whitespace;
- every statically resolvable named SQL parameter must have exactly one supplied
  parameter binding and no supplied binding may be unused;
- statically resolvable `alias.column` references must exist in the canonical Flyway
  schema; schema compatibility baselines must not drift from the current modular
  schema;
- every contract GET is exercised through Spring and PostgreSQL, including optional
  query/filter branches where the contract provides them;
- important write/read round trips receive explicit domain happy-path integration
  tests in addition to the broad transport smoke sweep;
- an unexpected HTTP 5xx is always a regression. Do not weaken the expected status
  or catch the exception merely to make the test green; trace the first server-side
  exception to its SQL/mapper/service root cause and add a regression at that route.

`python3 infrastructure/scripts/quality/audit_sql_runtime.py` is part of the normal
quality gate. `mvn verify` remains authoritative for real Spring/JDBC/PostgreSQL
behavior that static analysis cannot resolve.

## Backend correctness and security

- Java 21, constructor injection and explicit domain boundaries are mandatory.
- `openapi/openapi.json` is the external HTTP specification. It generates only
  immutable API DTOs. Module controllers own Spring MVC mappings and validate
  request DTOs directly with Bean Validation; `audit_controller_contract.py`
  fails on route, parameter, body, media-type or response drift. A generated
  runtime `contract`/`*Api` interface layer is forbidden.
- Typed validated DTOs and MapStruct use fail-closed mappings; unmapped target
  fields are compilation errors.
- Spring Security is the sole authentication and authorization boundary. Mutating
  browser requests retain session/JWT validation as applicable, CSRF, host and
  origin controls. Endpoint-local authentication shortcuts are prohibited.
- Transactions encompass a business mutation and its required audit record.
- SQL remains parameterized and belongs to the owning module's repository layer.
  Services contain no SQL literals and do not access the generic JDBC executor.
  User-controlled identifiers, sort clauses or SQL fragments require an explicit
  allow-listed mapping.
- Generated HTTP request and response DTOs live exclusively in
  `eu.royalblackwater.api.dto`; module-internal transition DTOs live in the owning
  module's `dto` package. Generic `model` packages are forbidden because they hide
  ownership. Controllers and public service signatures expose neither entities nor
  raw database/JSON row maps, and typed query parameters are never rebuilt as raw
  maps before validation.
- Every HTTP module owns a mapper layer for DTO/entity/row transitions. Untyped
  `ResponseEntity<?>`, controller-side body recasting, generic contract-conversion
  services and direct entity exposure are architecture violations. ObjectMapper
  conversion is permitted only inside an explicit mapper for genuinely dynamic
  integration/control-file JSON, never as a generic application-layer shortcut.
- Java imports must be explicit, resolvable and used. Wildcard imports, duplicate
  imports, unused imports and unresolved project-internal imports are repository-gate failures.
  DTO/mapper changes must compile with Maven; parser-only syntax checks are not
  sufficient evidence for generic conversions, constructor signatures or MapStruct.
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
  `infrastructure/scripts/quality/audit_spring_backend.py` enforces static invariants.
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
- Releases follow `MAJOR.MINOR.PATCH` as defined in
  `docs/development/VERSIONING.md`: fixes increment Patch, compatible features
  increment Minor, and incompatible or explicitly major extensions increment
  Major. Published versions are immutable.
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
- Script ownership is explicit: only `deploy.sh` and `update.sh` are public root
  wrappers. Shared scripts live in responsibility-based modules under
  `infrastructure/scripts/`: `quality/`, `generation/`, `release/` and focused
  runtime modules. The deployment packager uses an explicit allowlist, so
  repository-only quality/generation code does not ship to production. Do not
  recreate a top-level `scripts/` or duplicate proxy copies.
- Helpers under `.agents/scripts/` and `frontend/scripts/` stay with their
  owning module and may not become general-purpose cross-repository logic.
- Production diagnostics are read-only, bounded and redacted at the trusted
  origin. Raw target logs are not persisted as convenience artifacts and agent
  inputs exclude credentials, query values, email addresses and complete IPs.
- The API never gains direct host root privileges. Privileged actions cross the
  documented owner-only request boundary to root-owned systemd runners.

## Documentation and agent assistance

- Behavior, configuration, migration and operations documentation change in the
  same commit as the implementation.
- `docs/README.md` is the human documentation index. `AGENTS.md` points agents to
  `.agents/ONBOARDING.md`, which in turn references `.agents/PROJECT_CACHE.md` and
  live helper scripts.
- `docs/architecture/MODULE_CATALOG.md` documents every backend, frontend and
  infrastructure module. `.agents/MODULE_CACHE.md` is its compact routing layer;
  the documentation gate compares both with the actual module directories.
- Durable debugging conclusions live in an appropriate runbook and are mirrored
  compactly in `.agents/DEBUGGING_CACHE.md`. Raw incident data never becomes a
  cache.
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
`python3 infrastructure/scripts/quality/check_repository.py --strict-tree` must pass. A skipped toolchain,
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
