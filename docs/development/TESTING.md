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
2. Flyway empty-database and supported-upgrade tests.
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
11. Shell syntax, Compose, container and repository hygiene checks.

A release is not production-ready when Maven, frontend build, PostgreSQL integration tests or container builds were skipped. Local quick mode may skip unavailable toolchains, but CI may not.

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

`ApiSurfaceIntegrationTest` reads the canonical OpenAPI contract and turns the
complete operation inventory into a runtime no-5xx sweep. Every GET is executed
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

Dependency suppressions are exceptional and must remain narrow, documented, time-bounded, and self-removing. The current `spring-api/dependency-check-suppressions.xml` entry for **CVE-2026-66299** applies only to `org.apache.tomcat.embed:tomcat-embed-core:11.0.24`. Apache documents the issue as affecting the Tomcat WebSocket chat **example application**; WoSB embeds Tomcat and does not package or deploy the Tomcat examples web application. The suppression therefore records an applicability decision rather than lowering the global CVSS gate.

The suppression must be removed as soon as embedded Tomcat is **11.0.25 or newer**, or immediately if Apache broadens the affected scope. CI uses `failBuildOnUnusedSuppressionRule=true`, so an upgrade that makes the exact `11.0.24` suppression unused intentionally breaks the security job until the obsolete rule is deleted. The rule also expires on **2026-09-08 UTC** as a second fail-closed review deadline. Do not extend that date without re-reading the upstream Apache advisory and recording a new review.

The normal high-severity gate remains `failBuildOnCVSS=7`. Never suppress by broad CVSS range, wildcard vulnerability name, entire Tomcat family, or generic CPE just to make CI green.

### Security operations fixtures

`infrastructure/scripts/quality/tests/tls-environment-safety.sh` is the regression gate for Test/Production TLS isolation. It functionally validates certificate/key/hostname matching and statically requires Production to reject self-signed/ACME-staging configuration. `frontend/tests/fileUploadSecurity.test.mjs` keeps browser-side upload limits aligned with the backend envelope; backend type/signature/quota checks remain authoritative. Mandatory infrastructure quality gates must only depend on declared baseline host tools; the TLS gate uses `grep` rather than optional developer tooling such as `ripgrep`, because `update.sh` executes the same gate on deployment hosts.
