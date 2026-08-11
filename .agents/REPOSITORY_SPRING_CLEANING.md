# How-to: Repository Spring Cleaning

This guide organizes a broad quality pass with minimal repeated analysis. It is a
workflow, not a second technical specification. In case of conflicts,
`AGENTS.md`, `docs/development/QUALITY_STANDARDS.md`, and the primary sources
linked there take precedence.

## 1. Define goals and boundaries

A spring cleaning pass should measurably improve maintainability, security,
reproducibility, or operational stability without casually changing product
behavior. Before the first edit, record:

- affected quality attributes and subtrees;
- measurable symptoms such as duplication, wrong dependency direction, unclear
  ownership, unbounded lists, unreliable CI, or outdated documentation;
- behavior and external contracts that must explicitly remain unchanged;
- required focused tests and the final gate.

Do not disguise cosmetic mass reshuffling, speculative abstraction layers, or
simultaneous product expansion as “cleanup.” Other people's changes, generated
output, published Flyway migrations, and history remain untouched.

## 2. Token-efficient entry

```bash
bash .agents/scripts/project-context.sh
sed -n '1,280p' .agents/PROJECT_CACHE.md
sed -n '1,260p' .agents/MODULE_CACHE.md
bash .agents/scripts/check-changes.sh
```

Then read only the primary sources for the actual scope:

| Scope | Primary sources |
| --- | --- |
| Overall quality | `AGENTS.md`, `docs/development/QUALITY_STANDARDS.md` |
| Module boundaries | `docs/architecture/MODULE_CATALOG.md`, `.agents/MODULE_CACHE.md` |
| Debugging | `docs/debugging/MODULE_DEBUGGING.md`, `.agents/DEBUGGING_CACHE.md` |
| Backend/API | `docs/architecture/ARCHITECTURE.md`, `docs/reference/API.md`, `openapi/openapi.json` |
| Frontend/CSS | `frontend/ARCHITECTURE.md`, `docs/reference/CSS_ARCHITECTURE.md` |
| Database | `docs/development/DATABASE.md`, affected migrations and upgrade tests |
| Infrastructure | `infrastructure/ARCHITECTURE.md`, `docs/deployment/OPERATIONS.md` |
| CI and gates | `docs/development/TESTING.md`, `Makefile`, `infrastructure/scripts/quality/validate.sh`, `.github/workflows/` |

Use `rg` first to find callers, tests, configuration, and documentation for a
responsibility. Do not read files broadly one by one when the cache and primary
source already identify the entry point.

Place scripts according to executable responsibility inside the central module
architecture: only `deploy.sh` and `update.sh` remain in the root; quality gates
live under `infrastructure/scripts/quality/`, generators under `generation/`,
packaging/deployment under `release/`, and host/runtime/recovery logic in the
respective domain modules. The runtime artifact includes only explicitly approved
modules. `.agents/scripts/` and `frontend/scripts/` are owner-bound helpers, not
general-purpose parallel trees.

## 3. Prioritize findings

Assign every finding a priority and evidence:

1. **P0 – Data/security:** data loss, authentication or authorization bypass,
   secret/PII leak, unsafe restore, or supply-chain issue.
2. **P1 – Correctness/operations:** broken contract, migration, deployment,
   rollback, reproducible build, or mandatory gate.
3. **P2 – Maintainability/performance:** mixed responsibilities, wrong dependency
   direction, N+1, unbounded list, or hard-to-test coupling.
4. **P3 – Order:** naming, local duplication, or placement without immediate
   failure risk.

Work only on substantiated findings. A large or unusual file size is a review
signal, but not by itself a reason to refactor. Close P0/P1 first in small,
individually verifiable changes.

## 4. Apply SOLID and KISS appropriately to the project

SOLID is a decision aid here, not a class counter:

- **One nameable responsibility:** transport binds, service decides, repository
  persists, mapper translates. Frontend pages compose, composables control flows,
  API modules transport, domain modules calculate.
- **Extend at the stable contract:** evolve the OpenAPI specification, generated
  API DTOs, module controllers, services, and infrastructure helpers instead of
  adding parallel dispatch, transport, or compatibility paths.
- **Substitutability:** use inheritance only for genuinely substitutable types;
  small composition and constructor injection are usually clearer.
- **Narrow interfaces:** pass only the data and operations a consumer needs; no
  generic manager, context, or utility catch-all objects.
- **Dependencies point inward:** business rules know HTTP, Vue, the file system,
  or concrete clients only when that is their actual responsibility.

KISS constrains implementation:

- first fix the smallest functionally complete cause;
- reuse existing abstractions;
- extract only when responsibility, lifetime, or testability becomes clearer;
- do not replace two readable local lines with a general framework;
- remove dead paths only after caller, configuration, documentation, and migration review;
- inspect files around 300–400 lines for meaningful split points, but do not evade
  the 420-line limit with content-free wrappers.

## 5. API, security, and privacy pass

For every affected operation, trace from contract to persistence:

```text
OpenAPI -> generated API DTO -> module controller -> service
             -> repository/mapper -> migration/index -> tests/documentation
```

Check:

- server-side authentication and authorization, including object and fleet scope;
  frontend guards do not count as a security boundary;
- session/JWT, CSRF, host, origin, and CORS for mutating browser requests;
- typed input validation, allowed sort fields, parameterized queries, bounded
  pagination, payload size, and upload types;
- transaction boundary including required audit entries;
- no lazy loads outside the transaction, N+1, or unbounded collections;
- concise 4xx errors and centralized 5xx diagnostics without payloads, secrets,
  tokens, complete IP addresses, or personal content;
- purpose, retention, and export/correction/deletion paths for new personal data;
- sparse, non-blocking webhooks and explicitly allowed outbound access.

Implement schema changes only as new, small Flyway forward migrations. Review
entity, index, empty database, supported upgrade, backup, and restore together;
Hibernate remains set to `validate`.

## 6. CI/CD and supply-chain pass

Treat workflows as executable production contracts:

- pin actions, runtimes, scanners, and test dependencies;
- install every used toolchain and test dependency explicitly;
- pass secrets only through secret/environment boundaries and do not pass empty
  optional secrets to tools as if they were real credentials;
- a cache is an acceleration, never a correctness prerequisite;
- create compiled JAR/frontend artifacts before image or release builds and ensure
  `.dockerignore` does not exclude them from build context;
- release artifacts remain source-free, inventoried, checksummed, and verified
  fail-closed before installation;
- containers remain read-only, capability-dropped, and free of embedded secrets;
- treat migration, backup, readiness, switch-over, and rollback as one workflow;
- do not hide scanner or test failures with `continue-on-error`, `failOnError=false`,
  or permissive fallbacks;
- choose realistic time limits for documented cold-start paths without allowing
  hangs to run indefinitely.

Specifically for OWASP/NVD: an empty cache contains several hundred thousand
records. Without an API key, verify only connectivity and correct key handling
locally; run the complete mandatory scan in the GitHub workflow with Maven cache
and preferably `NVD_API_KEY`.
Setting this GitHub secret requires no repository push: afterward restart the
security workflow with `gh workflow run security.yml` or rerun the failed run.

Commits are small, verified cleanup units; pushes are deliberately batched CI
boundaries. Because every push to `main` starts the NVD Dependency-Check, do not
push every local commit immediately. Before pushing, verify that the state forms
a meaningful complete CI unit and that the external scan actually needs to run again.

For every repaired CI contract, add a small static or dynamic regression check.
Validate workflow syntax and reproduce the exact previously failing command locally
where the environment allows it.

## 7. Structure without a large rewrite

Work in this order:

1. correct outdated or contradictory entry points and contracts;
2. fix wrong dependency directions at the smallest functional boundary;
3. split overloaded files along existing responsibilities;
4. move real duplicates into the already-responsible layer after tests;
5. rename files/directories only when navigation and ownership become clearer;
6. remove dead files only after `rg`, build, runtime, packaging, and documentation review;
7. update architecture, operations, test, and `.agents` navigation in the same step;
8. compare module inventory against docs and quick cache with
   `bash .agents/scripts/check-cache.sh`.

Do not mechanically “complete layers”: a feature needs only the directories and
types for which it has real responsibilities.

## 8. Implement changes in verifiable passes

Handle only one cause or tightly coupled invariant per pass:

1. Reproduce the original failure with the smallest suitable command.
2. Read callers, test, configuration, and documentation.
3. Fix the cause with the smallest complete diff.
4. Add a regression test and run it in focused form.
5. Use `bash .agents/scripts/check-changes.sh --run`.
6. Only after several passes, run the full gate:

```bash
python3 -m pip install -r requirements-ci.txt
bash .agents/scripts/check-all.sh
```

Let long-running processes finish in the same session. Do not poll tightly,
restart because of quiet phases, or request repeated full output. Evaluate only
completion or an actionable failure.

When a local toolchain, Docker/port sandbox, or external service is unavailable,
explicitly distinguish the environment blocker from a product failure and rerun
only the missing part in a supported environment.

### Post-feature cleanup checklist

After a large feature lands, use its sibling routes or flows as the primary
comparison surface. This catches integration debt that a file-size inventory
usually misses:

- compare create/edit/view/print templates for repeated document structures; if
  the structure is one presentation contract with multiple consumers, give it
  one component owner;
- inspect new `domain/` files for `window`, DOM, Vue, network, storage, or file
  system access. Move browser or infrastructure integration to the feature root,
  a composable, or the responsible service instead of weakening the domain
  boundary;
- inspect joined SQL row maps for generic collisions such as `id`, `created_at`,
  and `owner_id`. Alias every value used for a business decision and test with
  deliberately different aggregate and joined-resource IDs;
- exercise public/share routes both anonymously and as a different signed-in
  user. Confirm the intended authorization contract before making supporting
  catalogs public or treating authenticated enrichment as anonymous behavior;
- trace every new persisted file through upload optimization, publication,
  deletion, backup, restore, and recovery-client validation;
- prefer behavior regressions. Source-text assertions are appropriate only for
  declarative or operational invariants that cannot reasonably execute in the
  focused test environment.

Finish the pass with `rg` for the removed path or responsibility, `git diff
--check`, the focused module tests, strict-tree validation, cache validation, and
the full gate. Record any deferred finding with evidence and a bounded next step.

## 9. Completion criteria

The spring cleaning is complete when:

- every implemented finding has a substantiated cause and matching regression check;
- behavior, contract, configuration, migration, and documentation agree;
- security, privacy, performance, and recovery consequences were reviewed;
- focused gates and `make validate` pass without hidden skips;
- generated files, local environments, and other people's changes remain untouched;
- `git diff --check`, strict repository validation, and working-tree checks are clean;
- remaining findings are documented with priority, evidence, and the next safe step.

Commit or push are not part of spring cleaning unless explicitly requested.

### Vulnerability suppressions are temporary architecture debt

Dependency-Check suppressions are treated like temporary compatibility debt: exact dependency + exact CVE, explicit reason, expiry, upstream removal condition, and automated unused-rule detection. The daily security job must refresh its vulnerability database before scanning. Never make the CVSS threshold more permissive to accommodate a single disputed finding.

For the current Tomcat exception, `CVE-2026-66299` may only be suppressed for `tomcat-embed-core:11.0.24` because the reviewed Apache advisory scopes the defect to the WebSocket chat example application, which is not deployed by WoSB. Delete the rule when Tomcat reaches `11.0.25+`; `failBuildOnUnusedSuppressionRule=true` exists specifically to force that cleanup.

### Security backlog completion rule

A security TODO is not complete merely because code exists. Convert it into a repeatable invariant: a quality test or integration test plus durable documentation. For TLS, Production must fail closed on staging/self-signed configuration and certificate material must be validated before swap. For uploads, frontend checks never replace backend type/signature/quota enforcement. For deployment, private target environments/certificates stay outside immutable artifacts and databases are not host-published in release compose.
