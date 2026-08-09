# Testing

Run the complete gate with:

```bash
python3 -m pip install -r requirements-ci.txt
make validate
```

The pinned Python test dependency is installed explicitly because hosted Python
runtimes do not include `pytest`. Repository audit scripts themselves continue to
use only the Python standard library.

It includes:

1. Spring unit and integration tests with PostgreSQL Testcontainers.
2. Flyway empty-database and supported-upgrade tests, including forward migration
   discovery instead of brittle hard-coded migration counts.
3. Spring Security, session, CSRF and authorization tests.
4. API operation coverage for every currently generated contract operation. The
   repository gate regenerates the Spring route adapters in memory and reports a
   bounded per-file diff when contract, controller or operation catalog drift.
5. MapStruct compilation with unmapped targets as errors.
6. Build-calculation golden cases.
7. Query batching/N+1 invariants and list-filter tests.
8. Vue unit, locale, binding, responsive, production-build and Chromium browser
   smoke checks for navigation, accessibility and critical forms.
9. Release artifact inventory, tamper and safe-extraction tests.
10. Backup-set and recovery-bundle contract tests.
11. Target-aware recovery-tool enrollment, dual-profile and current Spring/Flyway
    remote-sync contract tests.
12. Shell syntax, Compose, container and repository hygiene checks.
13. Backend test-completeness auditing: every production Java class must belong to exactly one explicit test strategy and every production backend module must own module-local tests. Every discovered business component additionally requires a module-local focused semantic test; the global executable surfaces then invoke every discovered business-layer public entry point (including components outside a direct `service/` directory), every OpenAPI operation, every generated DTO runtime contract, every module-local DTO record and every JPA entity read surface. Focused regressions cover stateful entity transitions, request/session filters, controller response helpers, persistence primitives and Build payload/snapshot normalization.
14. JaCoCo go-live gates: at least 80% line coverage, 65% branch coverage and 80% method coverage across analyzed backend code, at least 60% line coverage per analyzed package, and zero completely missed production classes in those packages. Only generator-owned root OpenAPI DTOs and static SQL catalogs are excluded from the percentage metric because they have dedicated generated-contract and SQL/schema audits; module-local DTOs, JPA entities, filters, configuration, controllers, repositories, mappers and business components remain in executable coverage.

A release is not production-ready when Maven, frontend build, PostgreSQL integration tests or container builds were skipped. Local quick mode may skip unavailable toolchains, but CI may not. The JaCoCo thresholds are release floors, not a claim that a numeric percentage proves correctness; focused success, failure, permission and state-transition tests remain mandatory for changed business behavior.

## Release verification after local patch application

Patch files under `patches/` are transport artifacts only. After applying a patch, verify the
working tree itself; do not treat a successful `git apply` as test evidence. For backend or
cross-cutting release work, the final local Maven proof is a clean run from the physical Spring
project directory:

```bash
cd spring-api
pwd -P
realpath pom.xml
mvn clean verify
```

The run must reach Surefire, packaging, the JaCoCo report and the JaCoCo check. A Surefire
success followed by a JaCoCo failure is still a failed release gate. Do not lower thresholds or
broaden exclusions to make a release pass; add focused tests for the missing behavior. Generic
surface and branch-matrix tests supplement semantic module tests and may probe expected domain
validation errors, but they must not manufacture invalid internal objects or tolerate unsafe JVM
errors such as harness-caused `NullPointerException`/`ClassCastException`.

If Maven output names an unexpected absolute `target` or Surefire-report path, stop and verify
`pwd -P`/`realpath pom.xml` before debugging source code. `mvn clean` cleans the project it is
actually invoked against; it does not discover or switch to a newly extracted repository tree.

## NVD API key for the security workflow

The OWASP dependency scan accepts the optional repository secret
`NVD_API_KEY`. Set or rotate it from an authenticated local GitHub CLI without
placing the value in shell history, source files or workflow arguments:

```bash
gh secret set NVD_API_KEY
```

The command reads the value interactively. The workflow passes a non-empty key
through the plugin's environment-variable integration; pull requests without
secret access use the slower public NVD path. Never print the key to verify it.
GitHub exposes only secret metadata, not the stored value.

Creating or rotating the secret changes GitHub configuration, not repository
content. It therefore needs no trigger commit or push. Start a fresh security
run explicitly, or rerun the failed workflow after setting the secret:

```bash
gh workflow run security.yml
gh run list --workflow security.yml --limit 5
# Alternatively, for a known failed run:
gh run rerun <run-id> --failed
```

The newly started or rerun job reads the current secret value. Verify only the
workflow result; do not attempt to read the secret back.

## Scope-based development checks

Use focused feedback during implementation, then run the required release gate:

```bash
bash .agents/scripts/check-changes.sh         # show checks for the current diff
bash .agents/scripts/check-changes.sh --run   # run those existing gates
bash .agents/scripts/check-frontend.sh        # frontend tests/build with temporary env
bash .agents/scripts/check-docs.sh            # documentation references and repository checks
bash .agents/scripts/check-cache.sh           # module catalog/cache completeness
bash .agents/scripts/check-all.sh             # quiet wrapper around the full release gate
```

The frontend gate requires the Playwright Chromium runtime. Install it once with
`npx playwright install chromium` from `frontend/`; CI installs Chromium and its
system dependencies explicitly before running the gate.

Agent wrappers suppress successful tool chatter to conserve context and print a
bounded failure tail. Set `AGENT_GATE_VERBOSE=1` only when the complete underlying
output is needed for diagnosis.

`ApplicationIntegrationTest` starts the complete Spring application against a
PostgreSQL Testcontainer and exercises real HTTP behavior for public health and
registration, anonymous cookie-consent persistence, sessions, administrator
authorization, CSRF, origin checks and bounded error responses. Its domain happy
paths create and reload Fleet/Squad, Build, Forum, Guide, Group and Calendar data
through HTTP so repository/mapper failures cannot hide behind controller-only tests.
Run it in isolation with:

```bash
mvn -f spring-api/pom.xml -Dtest=ApplicationIntegrationTest test
```

`BuildPrintoutIntegrationTest` owns the cross-boundary regression for the versioned
Build printout cache. It creates a real Build, stores and downloads a PNG over HTTP,
proves that the identical cache identity is reused without a second audit mutation,
changes the business Build, verifies metadata/file invalidation and regenerates the
new version. `BuildPrintoutServiceTest` separately covers stale revisions, conflicting
bytes, cache reuse, invalidation and cleanup behavior at the service/filesystem edge.

The Spring integration suites enable `rbf.diagnostics.http-lifecycle-logging=true`.
Every API response still receives `X-Request-Id` when lifecycle telemetry is disabled;
when enabled the test output contains `api_request_start`/`api_request_complete` with
request ID, method, normalized route, status and duration. This is intended for
automated correlation and short diagnostic runs, not persistent visitor analytics.

`ApiSurfaceIntegrationTest` reads the assembled OpenAPI compatibility artifact and turns the
complete operation inventory into a runtime no-5xx sweep. It also executes every operation anonymously to verify the public/protected authentication boundary and sends every authenticated non-bootstrap write without a CSRF token to require HTTP 403 before controller mutation logic. Every GET is executed
against the real Spring application and PostgreSQL at least once; GETs with optional
query parameters are executed again with the optional filters populated to activate
dynamic SQL branches. Non-GET operations are exercised at the transport boundary
without destructive domain mutations. Body probes follow the OpenAPI media type:
JSON operations receive malformed JSON, while multipart operations receive multipart
framing with a missing required part. A second multipart-only negative case sends
JSON deliberately and requires HTTP 415, so content-negotiation/binding failures do
not masquerade as domain failures. Any response >= 500 fails the suite. Run it
with:

```bash
mvn -f spring-api/pom.xml -Dtest=ApiSurfaceIntegrationTest test
```

The surface sweep is deliberately not the final word for stateful administration and
review workflows. Endpoints that consume or mutate persisted state must also have a
real lifecycle regression in `ApplicationIntegrationTest`: create or submit the
prerequisite data, read it through the user-facing list/detail route, perform the
transition, and verify a meaningful follow-up read. Review flows must cover both
approve/complete and reject branches where they exist, and repeating an already
consumed transition must return a bounded 4xx rather than 500. Prefer real fixture IDs
over impossible sentinel IDs whenever doing so reaches repository/mapper logic safely.

Registration Access Review is the reference flow:
`register -> pending list -> status=all -> approve -> login -> approved list`, plus an
independent `register -> pending -> reject -> rejected list` branch. The broader
administration regression also round-trips user moderation, Build-role CRUD, privacy
review and IP block/unblock. Together, the contract surface sweep, SQL runtime audit
and stateful lifecycle tests are three independent layers; none replaces either of
the others.

Backend test inventory also has a dependency-free structural gate:

```bash
python3 infrastructure/scripts/quality/check_backend_test_coverage.py
```

It discovers backend modules directly from `spring-api/src/main/java`, requires a module-local test for every production module, classifies every production Java class into exactly one explicit test strategy, inventories controllers, repositories, mappers, entities, generated and module-local DTOs, filters and business components, and rejects any business component that is only present in the generic surface without a module-local focused semantic test. It also verifies the global business/API/DTO/entity/integration strategy files and that the Maven JaCoCo release floors and narrow exclusion policy cannot silently regress. The executable `BackendServiceSurfaceTest` discovers business-layer classes recursively across the backend (not only direct `service/` packages), creates deterministic type-correct record/DTO boundary values and invokes every public entry point with mocked collaborators whose collection, array, save-style and record returns preserve the declared runtime shape. `ModuleDtoContractTest` and `PersistenceEntityContractTest` keep hand-written DTO/entity classes executable, while focused tests own semantic state-transition and validation assertions. These global tests are crash/wiring safety nets; module-focused tests still own business correctness.

SQL assembly also has a dependency-free static gate:

```bash
python3 infrastructure/scripts/quality/audit_sql_runtime.py
```

The SQL runtime audit checks statically resolvable fragment boundaries, named
parameter parity, table and alias/column references against the Flyway schema and
compatibility schema drift. It complements rather than replaces PostgreSQL integration tests:
dynamic SQL and mapper behavior remain runtime concerns. The audit itself has
regression fixtures for merged named parameters, retired relations and invalid
alias/column references in `tests/quality/test_sql_runtime_audit.py`; they run as part
of the repository validation pytest phase.

Mockito is loaded as an explicit JVM startup agent. Maven resolves the agent path
through `maven-dependency-plugin`, so default and overridden local repositories
use the same configuration and tests never rely on dynamic self-attachment.

Controller/OpenAPI route drift can be diagnosed without starting Docker or Spring:

```bash
python3 infrastructure/scripts/quality/audit_controller_contract.py
python3 infrastructure/scripts/generation/generate_api_dtos.py --check
```

The controller audit covers all 177 operations and compares HTTP method/path,
path/query bindings, request DTO/media type and successful response type against
OpenAPI. DTOs remain generator-owned; controller mappings are handwritten and
module-owned, so there is no route-generator regeneration step.

The Playwright suite starts Vite and replaces only `/api/` requests with
deterministic browser fixtures. It verifies browser-side navigation, cookie-setting
reloads after transient API failures and form contracts without weakening the
Spring integration boundary. Run it with:

```bash
cd frontend
npm run test:browser
```

The helpers do not implement separate assertions. They delegate to `make`, the
existing test scripts and the strict repository checker. A failed or skipped
check remains failed/skipped even when the cause is a local sandbox or missing
toolchain; record the limitation and rerun it in a supported environment.

`check-cache.sh` is the narrow exception: it asks the canonical documentation
checker to compare the real backend, frontend and infrastructure module
directories with both the primary module catalog and the agent quick cache. It
detects missing navigation entries, while review remains responsible for the
semantic accuracy of their descriptions.

For frontend changes, test logic, page bindings, locales, responsive invariants,
critical browser flows and a production build. Backend changes require Maven
compilation/tests and, when persistence is involved, PostgreSQL/Testcontainers.
Infrastructure changes require the infrastructure/update contract suites; backup,
migration or recovery changes also require the recovery tests.

## Daily dependency vulnerability cache and temporary suppressions

The `Security` GitHub Actions workflow refreshes OWASP Dependency-Check's NVD/cache data **daily at 04:17 UTC** and then scans the Spring dependency graph from that refreshed cache. The cache is stored under Maven's Dependency-Check data directory and uses a date-scoped GitHub Actions cache key so the previous day's database can be restored and incrementally refreshed instead of performing a cold NVD import on every run.

Dependency suppressions are exceptional and must remain narrow, documented, time-bounded, and self-removing. The previous **CVE-2026-66299** exception was removed after embedded Tomcat was upgraded from **11.0.24** to the patched **11.0.25** release. The suppression XML and NVD policy remain in the repository as empty, validated extension points for future cases.

CI uses `failBuildOnUnusedSuppressionRule=true`, so an upgrade that makes a future exact suppression unused intentionally breaks the security job until the obsolete rule is deleted.

The normal high-severity gate remains `failBuildOnCVSS=7`. Before Dependency-Check runs, `check_dependency_suppressions.py` reads the versioned `spring-api/dependency-suppression-policy.json` and queries the NVD CVE API. A policy with `action: allow-unfixed-only` fails when NVD explicitly reports a newer fixed version for the named product; it also fails closed when NVD cannot be queried. NVD version metadata is not guaranteed to be complete, so the XML expiry and the exact package selector remain mandatory second controls. Never suppress by broad CVSS range, wildcard vulnerability name, entire Tomcat family, or generic CPE just to make CI green.

### Security operations fixtures

`infrastructure/scripts/quality/tests/tls-environment-safety.sh` is the regression gate for Test/Production TLS isolation. It functionally validates certificate/key/hostname matching and statically requires Production to reject self-signed/ACME-staging configuration. `frontend/tests/fileUploadSecurity.test.mjs` keeps browser-side upload limits aligned with the backend envelope; backend type/signature/quota checks remain authoritative. Mandatory infrastructure quality gates must only depend on declared baseline host tools; the TLS gate uses `grep` rather than optional developer tooling such as `ripgrep`, because `update.sh` executes the same gate on deployment hosts.
