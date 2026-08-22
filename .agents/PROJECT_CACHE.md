# Project Cache for Repository Agents

> Reviewed on 2026-08-11. This cache is a navigation index, not an authoritative
> source. Before making changes, always read `AGENTS.md`, the affected files,
> callers, tests, configuration, and documentation. In case of conflict, the
> source code or the primary source named below takes precedence.
>
> New agent? Read [ONBOARDING.md](ONBOARDING.md) first; it contains the shortest
> safe entry point, including the live snapshot and check selection.

## Quick overview

- Product: **Royal Blackwater Fleet**, a fleet operations portal for World of
  Sea Battle. Always read the current version from `VERSION`.
- Runtime: `Browser -> NGINX -> Spring Boot API -> PostgreSQL`.
- Backend: Java 21, Spring Boot 4.1, Maven 3.9, Spring Security, JPA/JDBC,
  MapStruct, Flyway, PostgreSQL, and Testcontainers.
- Frontend: Vue 3.5, Vue Router 4, Vite 8, Node 22, and Playwright Chromium;
  application code remains JavaScript, with incremental TypeScript checking for
  complex domain modules.
- Operations: Docker Compose, NGINX, systemd runners, and artifact-based release,
  update, backup, and restore workflows.
- The former Python backend is no longer part of the runtime. Python is used for
  repository, infrastructure, packaging, and recovery tooling.

## Authoritative entry points

| Topic | Read first |
| --- | --- |
| Working rules | `AGENTS.md`, `docs/development/QUALITY_STANDARDS.md`, `docs/development/VERSIONING.md` |
| Overall system | `README.md`, `docs/architecture/ARCHITECTURE.md` |
| Module responsibility | `docs/architecture/MODULE_CATALOG.md`, `.agents/MODULE_CACHE.md` |
| Debugging | `.agents/DEBUGGING_CACHE.md`, `docs/debugging/MODULE_DEBUGGING.md` |
| Backend | `spring-api/README.md`, `spring-api/pom.xml`, `spring-api/src/main/resources/application.yml` |
| Frontend | `frontend/ARCHITECTURE.md`, `frontend/package.json`, `docs/reference/CSS_ARCHITECTURE.md` |
| Database | `docs/development/DATABASE.md`, `spring-api/src/main/resources/db/migration/` |
| Legacy data migration | `docs/debugging/LEGACY_BUILD_DATA_MIGRATION.md` |
| Tests | `docs/development/TESTING.md`, `Makefile`, `infrastructure/scripts/quality/validate.sh` |
| Broad quality cleanup | `.agents/REPOSITORY_SPRING_CLEANING.md` |
| Infrastructure | `infrastructure/ARCHITECTURE.md`, `infrastructure/README.md`, `infrastructure/compose.yml` |
| Operations/recovery | `docs/deployment/OPERATIONS.md`, `docs/deployment/DISASTER_RECOVERY.md` |
| HTTP contract | `openapi/source/` (authoring source), `openapi/openapi.json` (generated) |
| Webhooks/build data | `spring-api/src/main/reference/webhook-events.json`, `spring-api/src/main/reference/build-stats/` |

The documentation index is `docs/README.md`. Changes to behavior or operational
procedures include the associated documentation.

## Repository map

```text
spring-api/      sole backend runtime, security, business domains, persistence
frontend/        Vue application, feature modules, localization, and UI tests
openapi/         versioned external HTTP specification
infrastructure/  Compose and central script modules for quality, generation, and runtime
tests/recovery/  language-neutral recovery/remote-sync contract tests
docs/            architecture, development, operations, reference, and audits
patches/         local patch/download workspace; only `.gitkeep` is versioned
.github/         CI, security, release, and deployment workflows
```

Do not edit or version by hand: `frontend/src/locales/generated/`,
`frontend/dist/`, `node_modules/`, `spring-api/target/`, Python caches, local
`.env` files, runtime data, release artifacts, or patch payloads under `patches/`.
The existing `release/` and `release-arm64/` directories are generated/ignored
output. `patches/` intentionally remains present for local transfer/download use,
but Git history and `CHANGELOG.md` are the authoritative record of applied work.

## Backend navigation

The complete path-specific module inventory with responsibilities and diagnostic
entry points is in `docs/architecture/MODULE_CATALOG.md`; the token-efficient
selection is in `.agents/MODULE_CACHE.md`. Do not infer module responsibility from
a directory name alone.

- Composition/cross-cutting: `config`, `core`, `operations`, `persistence`, `shared`,
  and the generated `api/dto` transport models.
- Business domains: `account`, `audit`, `builds`, `calendar`, `content`, `files`,
  `fleet`, `forum`, `groups`, `guides`, `legal`, `masterdata`, `onboarding`,
  `privacy`, `raidhelper`, `security`, `securityops`, `ships`, `squads`, `strategies`,
  `warehouse`, `webhooks`.
- `openapi/source/` defines the external HTTP transport; `openapi/openapi.json` is
  composed deterministically, and generated `api/dto/*` records represent its
  request/response types. Module controllers own the Spring MVC bindings directly;
  missing, duplicate, or divergent routes fail `audit_controller_contract.py`.
- Controllers orchestrate only and know neither entities nor repositories.
  Authorization, business logic, transactions, and required audit work belong in
  services; persistence access goes through module repositories. Public service
  boundaries carry API or module DTOs, not JDBC rows, raw maps, or entities.
  Row/entity conversion belongs in mappers.
- Spring Security is the only security boundary. Router/UI guards are UX only.
  Private mutations require session, CSRF, and host/origin checks.
- Hibernate: `ddl-auto=validate`, `open-in-view=false`; responses must not trigger
  lazy-load queries. Growing lists need bounded search, pagination, and domain
  filters; load collections in batches/projections.
- MapStruct compiles with `unmappedTargetPolicy=ERROR`. Java files with executable
  responsibilities generally remain below 420 lines. Hand-maintained JSON sources
  follow the same 420-line limit and are split by responsibility under
  `openapi/source/`, `main/reference/build-stats/`, and the seed subdirectories;
  details: `docs/development/JSON_CATALOGS.md`. The same hard limit applies to
  executable frontend JavaScript modules; only the audited declarative locale
  modules and `autoLocalizationCatalog.js` are exempt.
- Mockito is loaded in the Maven test process as an explicit startup agent; the
  dependency property resolves the path even when the local Maven repository differs.
  Dynamic self-attach is not part of the test workflow. Generic surface/branch harnesses
  must construct internally valid objects and type-correct collaborator returns; expected
  domain validation exceptions are acceptable probes, but harness-caused `NullPointerException`,
  `ClassCastException`, linkage errors, or mixed Mockito raw/matcher arguments are test defects
  to fix rather than production failures to suppress.
- Schema changes only as new immutable Flyway migrations. Existing systems retain
  the unchanged V1 history; new databases use the B2 marker and the domain-separated
  V3–V7 migrations. New schema work starts as a small forward migration from V8 onward.
- Reference data lives under `spring-api/src/main/resources/seed` and is applied
  idempotently; preserve administrative overrides deliberately.

## Frontend navigation

- Entry point: `frontend/src/main.js`; routing: `frontend/src/router/index.js`.
- Feature modules live under `frontend/src/modules/<feature>/` and use `api/`,
  `domain/`, `composables/`, `components/`, and `pages/` as needed.
- Dependency direction: `page -> composable -> api/domain` and `page -> component`.
  Pages do not call APIs directly and do not own asynchronous workflows.
- Route modules exist for Accounts, Admin, Builds, Calendar, Combat, Fleet, Forum,
  Groups, Guides, Onboarding, Privacy, Legal, Squads, the Strategy Planner, and Warehouse.
- Transport belongs in API modules, deterministic rules in `domain`, state,
  lifecycle, and flows in composables, and reusable UI in components.
- Shared infrastructure: `core/`, `shared/`, `config/`, `router/`, `locales/`,
  and `styles/`.
- Vite environment values used by production code must be referenced statically
  (`import.meta.env.VITE_*`), never through `import.meta.env[name]`; dynamic access
  can pass `.env` validation but is not replaced in the production bundle.
- Frontend guards check guest/user/content-author/staff/admin/fleet-management state
  but never replace server-side authorization. Shared-content mutation routes are
  reserved at the Spring Security boundary for `ROLE_MODERATOR` and `ROLE_ADMIN`;
  ordinary users retain visible-content reads plus profile, password, privacy,
  group-join, and fleet-application self-service flows. Mirror the boundary through
  `canAuthorContent`/`requiresContentAuthor`, while keeping the backend authoritative.
  Fleet/squad management reads and capability flags also require staff in their domain
  services; legacy leadership membership metadata never elevates an ordinary account.
- Localization sources: `frontend/src/locales/messages/`; generator:
  `frontend/scripts/generate-locales.mjs`. English is the synchronous fallback;
  other locales load dynamically.
- Global CSS cascade: eight ordered imports from `frontend/src/styles/global/index.js`;
  order is an architecture contract. Feature styles remain with their modules.
- Build printing separates model construction (`buildPrintModel.js`), visual catalogs
  (`buildPrintVisualCatalog.js`), image embedding (`buildPrintImageEmbedding.js`), and
  SVG/document orchestration (`buildPrintExport.js`).
  Localization behavior lives in `autoLocalization.js`, with the large translation
  catalog separately in `autoLocalizationCatalog.js`.
- The Strategy Planner preserves its uploaded chart as a background layer and stores
  editable SVG overlay objects separately. Pointer coordinates must be transformed
  through the SVG screen matrix, and build references must match the marker ship on
  both the client and server. Its versioned document migrates legacy circle formations
  to ovals; new circles use one physical diameter. `strategyGeometry.js` changes object
  extent independently from fixed tactical strokes and arrowheads. Creation commands,
  selected-object properties, and size/rotation controls remain separate UI sections.
- The New Captain Guide is one Explorer-style knowledge workspace: a compact topic
  navigator opens each Markdown briefing and its typed Guide, Build, internal, or
  external resources in a wide reader. Search/type filters and topic cards live on the
  home view; mobile uses a topic picker instead of compressing the desktop navigator.
  Moderator editing operates on the same ordered hierarchy through a separate two-pane
  structure/editor workspace with collapsible resource cards; do not add a parallel
  content model.
- Browser smoke tests live under `frontend/tests/browser/`. They start Vite and mock
  only `/api/`; real security, session, CSRF, and origin boundaries are tested by
  `spring-api/src/test/java/eu/royalblackwater/api/integration/ApplicationIntegrationTest.java`
  against PostgreSQL.

## Infrastructure and operational boundaries

- The only public root entry points are `deploy.sh` and `update.sh`; both delegate
  to `infrastructure/scripts/release/deploy-from-origin.sh`. Production diagnostics
  start directly through `infrastructure/scripts/diagnostics/debug.sh`.
- `./deploy.sh --configure` is the complete interactive first run for the **test
  server**. Production is configured exclusively with
  `./deploy.sh --production --configure`; that dialog collects the public DNS name
  and Let's Encrypt email, then generates fresh production secrets and the private
  target environment locally on the target before continuing the deployment.
  Bootstrap credentials are not persisted in origin profiles; normal subsequent
  runs use only verified key access and `sudo -n`.
- Origin targets are strictly separated: `.env.origin.test` is the default for
  `deploy.sh`, `update.sh`, and diagnostics; `.env.origin.production` is loaded only
  after explicit `--production`. Do not allow automatic legacy fallback selection
  to `.env.origin`.
- Origin SSH identity material is external to the repository. Interactive relative names
  resolve below `$HOME/.ssh`; deployment, diagnostics, and build migration fail closed for
  any identity path that resolves below the source tree.
- Internal setup is split across `infrastructure/scripts/setup/{options,workflow,main}.sh`.
- Host helpers live under `infrastructure/scripts/lib/host/` (packages, storage,
  firewall, TLS, control); scripts must be robust, idempotent, and use clear exit
  codes. All shared repository scripts are modularized under `infrastructure/scripts/`:
  `quality/`, `quality/tests/`, `generation/`, `release/`, and the domain-specific
  runtime modules. Do not introduce a new top-level `scripts/` directory.
- The deployment packager copies runtime modules through an explicit allowlist.
  `quality/`, `generation/`, and the packaging scripts themselves must not appear
  in the production artifact. `.agents/scripts/` and `frontend/scripts/` remain
  owner-bound module helpers.
- The API executes no privileged host commands. It writes restrictive JSON requests
  into an inbox; root-owned systemd runners process them.
- Production uses compiled, checksum-protected, source-free artifacts. Origin transfer:
  `./deploy.sh`; update: `./update.sh`; both target the test server without a flag.
  Production requires `--production`. Target-server wrapper:
  `infrastructure/scripts/release/setup_website.sh`. Origin connections are stored
  separately in `.env.origin.test` and `.env.origin.production`; the corresponding
  `.example` files are templates. Verifier and rollback live under
  `infrastructure/scripts/release/`.
- Release Compose defaults are valid on a 1-vCPU VPS: PostgreSQL and API use CPU
  quotas of `1.0`, with `POSTGRES_CPU_LIMIT` and `API_CPU_LIMIT` available for larger
  targets. Memory cgroup warnings are host capability diagnostics; do not weaken the
  remaining read-only, capability, PID, network, and secret-file controls.
- Backup/restore couples the application, Flyway schema, persistent files, and the
  associated release artifact. Restore is staged and fail-closed.
- Strategy plans require no separate recovery channel: their rows and references are
  inside the unrestricted PostgreSQL dump, while chart backgrounds are inside the
  complete `uploads/` archive transferred by the recovery tool.
- A deliberately limited legacy partial restore (for example Python→Java builds) is,
  by contrast, a logical data migration against the already-current Flyway schema:
  do not import old numeric FKs, user/auth/master data, or DDL. Resolve references
  semantically, use exactly the same import file on test and then production, and
  require a complete transactional dry run before commit on both targets.
- Outbound networking is limited to explicit integrations. Webhooks contain concise
  audit/action notifications and must not be able to block the primary flow uncontrollably.

## Stable debugging starting point

- Use `.agents/DEBUGGING_CACHE.md` for initial symptom classification; the detailed
  layer-oriented workflow is in `docs/debugging/MODULE_DEBUGGING.md`.
- Primary deployment/update documentation: `docs/deployment/DEPLOYMENT.md` and
  `docs/debugging/2026-08-04-update-path-review.md`.
- Known production failures and verified causes: `docs/debugging/DEPLOYMENT_INCIDENTS.md`.
  Search there for the symptom first before remapping logs or flows from scratch.
- Collect production logs token-efficiently with `infrastructure/scripts/diagnostics/debug.sh`
  at the origin. Keep area, category, time window, line limit, and optional search text
  narrow. The remote collector writes nothing to the target; open only the redacted local
  file under `.diagnostics/` for agent analysis. Do not copy raw logs.
- Every API response receives a server-generated `X-Request-Id`. API failures are logged
  centrally as `api_error` with request ID, status, method, normalized path, and
  exception-related cause; security rejections remain separate as `security_401` and
  `security_403`. `RBF_HTTP_LIFECYCLE_LOGGING=true` enables start/complete logs with status
  and duration for tests/short diagnostics; default is `false`. Never log payloads, query
  values, cookies, client IP, or user agent.
- For 500s from calendar or staff date filters, first check for
  `MethodArgumentTypeMismatchException`. OpenAPI `date` and `date-time` must be bound
  explicitly as ISO in the route generator; browser UTC values carry `Z`. Transport
  binding failures are HTTP 400, not server errors.
- A master-data `UnrecognizedPropertyException` for `seed_checksum`, relational IDs, or
  helper columns means internal database fields reached the API contract unfiltered.
  Remove them at the mapper boundary; do not extend the public contract or loosen Jackson globally.
- Normalize a security-dashboard `ClassCastException` between `java.sql.Date` and
  `LocalDate` at the persistence boundary through `RowValues.date`.
- Gateway `stat()` failures on the maintenance marker indicate the missing additional
  runtime group 10001; status remains read-only, so do not broadly loosen permissions.
- The release workflow keeps PostgreSQL data under the shared installation root, creates
  coordinated backups before updates, lets Flyway migrate, and restores release and backup
  on failed activation. Never delete volumes or data directories as an attempted fix.
- Backup-server setup is a one-time three-step enrollment in the admin backup page: download
  the public request, run the generated checksum-verifying provisioner command on the backup
  host, and import the public response with a fresh host capability. The application-host
  timer and release installer already provide nightly and pre-update uploads; the standalone
  Recovery Tool is optional for listing, pulling, verifying, or restoring backup sets and is
  not a prerequisite for automated backups.
- The cookie-consent UI opens automatically without a saved decision and remains reachable
  in a fail-closed settings state when initialization fails. Manual opening remains available
  through the footer and privacy center.
- API usage and security boundaries are documented in `docs/reference/API.md`; the complete
  endpoint index is generated from `openapi/openapi.json` into `docs/reference/API_ENDPOINTS.md`.
- Historical audit snapshots are no longer maintained as a second documentation source.
  Current target rules live exclusively in architecture, development, reference, and
  operations documentation.

## Release rule

Every deployable state receives a new version. Bug fixes without a higher change class
increment at least `PATCH` by `0.0.1`; activated versions are never reused. Always read
the current base from `VERSION`.

## Common commands

```bash
make test          # fast check path that may skip unavailable toolchains
make validate      # complete release gate; identical to make test-full
make spring-test   # Maven verify
make sql-audit     # static SQL fragment/parameter/schema audit
make frontend-test # frontend tests, production build, and Chromium smoke tests
make check-tree    # strict repository hygiene
make build         # Spring package plus frontend build
make package-release
```

Before `make validate` or a direct `infrastructure/scripts/quality/validate.sh` run,
install the small, pinned Python test suite once with
`python3 -m pip install -r requirements-ci.txt`. CI and release workflows do this
explicitly after `actions/setup-python`; hosted Python runtimes do not reliably include
`pytest`.

Agent helpers for recurring inventory and check selection:

```bash
bash .agents/scripts/project-context.sh       # compact, always-current project/Git snapshot
bash .agents/scripts/check-changes.sh         # check recommendation from changed paths
bash .agents/scripts/check-changes.sh --run   # run recommended existing repository gates
bash .agents/scripts/check-backend.sh         # SQL runtime audit + Maven/PostgreSQL, compact output
bash .agents/scripts/check-frontend.sh        # frontend test/build/browser smoke with temporary .env
bash .agents/scripts/check-infrastructure.sh  # infrastructure/update contracts, compact output
bash .agents/scripts/check-docs.sh            # local Markdown links, commands, and doc generation
bash .agents/scripts/check-cache.sh           # compare module inventory in primary docs and quick cache
bash .agents/scripts/check-all.sh             # make validate with compact output
```

The helpers contain no independent business validation. They read the current state and
delegate to `make` and `infrastructure/scripts/quality/` so a second, eventually divergent
quality logic does not emerge. Documentation invariants live in
`infrastructure/scripts/quality/check_documentation.py`; `check-docs.sh` is only the
token-efficient entry point. Successful gates print one status line; failures print the
last 200 log lines. `AGENT_GATE_VERBOSE=1` enables full output for focused diagnostics.

Long-running gates, downloads, and container builds remain active in their existing process
session. To save tokens, do not poll tightly or repeatedly request full output; wait until
completion or an actionable failure, then continue with that result. Missing intermediate
output is not a reason to restart the same process.

The OWASP Dependency-Check downloads several hundred thousand NVD records when its cache is
empty. Do not babysit a keyless cold start locally to completion: after connectivity and
configuration have been demonstrated successfully, stop the local run and execute the
mandatory complete scan in the GitHub security workflow with Maven cache and preferably the
optional `NVD_API_KEY` secret. The secret is passed to the scanner as an environment variable
only when non-empty; the cache accelerates the run but never replaces the scan gate.
`gh secret set NVD_API_KEY` changes GitHub configuration and needs neither a commit nor a
trigger push. Then run `gh workflow run security.yml` or rerun a known failed run with
`gh run rerun <run-id> --failed`. The new run reads the currently stored secret value; never
try to print the key for verification.

The security workflow runs on every push to `main` and consumes the NVD service. Therefore,
keep changes locally in sensible, verified commits but batch pushes as a separate deliberate
action. Do not push after every small commit and do not create a push solely as an NVD-key or
cache test; start the existing workflow manually or rerun failed jobs when specifically needed.

Trivy scans API and gateway in sequential fail-closed steps. A finding in the API image therefore
prevents the gateway step from running. After a container security fix, always scan both completed
images separately and locally with the same Trivy cache; the Java scan downloads a large additional
database on the first run. Runtime Dockerfiles must run `apk upgrade --no-cache` before switching
to the unprivileged user.

The security scan of August 5, 2026 required targeted Spring Boot dependency overrides: Tomcat
`11.0.24` for the July fixes through `11.0.23`, Log4j `2.25.5` for `CVE-2026-49844`, and pgJDBC
`42.7.12` for `CVE-2026-54291`. These values are bound in `pom.xml` and `security_audit.py` as a
verified set that must be updated together; check new scanner findings against vendor advisories
first and do not suppress them indiscriminately.

`infrastructure/scripts/quality/validate.sh full` runs static repository, security, Spring, backend-test-completeness,
SQL-runtime, and CSS audits, Java syntax validation, infrastructure/update tests, recovery pytest,
`mvn verify`, frontend tests/build/Chromium smoke tests, and finally `--strict-tree`. The backend completeness gate requires a module-local test for every production module, classifies every production Java class into exactly one explicit test strategy, and rejects any business component that lacks a module-local focused semantic test in addition to the recursive executable public-entry-point surface. It inventories controllers, repositories, mappers, entities, generated/module DTOs, filters, configuration and persistence/shared helpers. Maven/JaCoCo then enforces the go-live floor of 80% lines, 65% branches and 80% methods overall, at least 60% lines per analyzed package, and no completely missed analyzed production class. Only generator-owned root OpenAPI DTOs and static SQL catalogs are excluded from the percentage metric; module-local DTOs, JPA entities and infrastructure-facing Java helpers remain covered by executable tests.
Install Playwright Chromium locally once with `npx playwright install chromium` inside `frontend/`.
For small changes, run focused tests first and then the affected gates; for cross-cutting changes,
run `make validate`.

## Change checklists

### API or backend domain

1. Trace the OpenAPI operation, API DTO, module controller, service, repository/mapper,
   security, and audit together.
2. Add success, failure, and permission cases; for lists, also test filters, bounds, and query count.
3. For review/admin/state-machine endpoints, test a stateful HTTP lifecycle: create prerequisite
   -> read list/detail -> transition -> follow-up read; test alternative decisions separately and
   a consumed transition as a controlled 4xx. `ApiSurfaceIntegrationTest`, SQL audit, and the
   lifecycle test are complementary.
4. No PII, tokens, complete IP addresses, or secrets in logs, errors, fixtures, or webhooks.

### Data model

1. Check entity/SQL usage and the recovery/upgrade path.
2. Add a new Flyway file; never modify published migrations.
3. Verify indexes for filtering/sorting, Hibernate validation, and restore behavior.

### Frontend feature

1. Keep flow in the composable, transport in API, pure rules in domain, and the page as composition
   only; reuse existing components/tokens.
2. Consider accessibility, responsive CSS, translations, and server-side authorization.
3. Run focused unit/domain tests plus page-binding, locale, responsive, browser, and build checks
   as relevant.

### Infrastructure/release/recovery

1. Read wrappers, callers, systemd/Compose contracts, and operations documentation.
2. Consider atomic file changes, idempotency, permissions, secret leaks, exit codes, and
   rollback/recovery.
3. Select appropriate infrastructure, update, artifact, tamper, and recovery tests.

## Cache maintenance

Recheck the cache when `AGENTS.md`, `README.md`, architecture/quality documents, `pom.xml`,
`package.json`, `Makefile`, `infrastructure/scripts/quality/validate.sh`, module directories, or
runtime/deployment topology change. Do not use ephemeral file counts, test counts, or contract
operation counts as decision inputs; obtain them directly with `rg`, `find`, or the relevant parser
when needed. For the transient state, run `bash .agents/scripts/project-context.sh` first so branch,
version, working tree, and debugging entry points do not need to be reconstructed from older session
summaries. `project-context.sh` also reports `agent_cache_status`; when it says `stale`, run
`bash .agents/scripts/check-cache.sh` first and add missing entries with functional context. A green
check proves inventory completeness, not that the descriptions are current.

### Daily dependency cache check and CVE-2026-66299 suppression

Security dependency analysis is intentionally **daily**, not weekly. `.github/workflows/security.yml` refreshes the OWASP Dependency-Check vulnerability cache first (`dependency-check:update-only`, `nvdValidForHours=0`) and then runs the scan with automatic updating disabled so the analyzed dataset is exactly the refreshed cache. The date-scoped cache under `~/.m2/repository/org/owasp/dependency-check-data` prevents repeated cold NVD imports while still producing a fresh daily cache generation.

`spring-api/dependency-check-suppressions.xml` currently contains one reviewed exception for `CVE-2026-66299` and **only** `pkg:maven/org.apache.tomcat.embed/tomcat-embed-core@11.0.24`. Reason: Apache limits the vulnerability to the WebSocket chat example application; the WoSB Spring Boot runtime embeds Tomcat and does not ship Tomcat's examples webapp. This is an applicability exception, not an acceptance of a vulnerable deployed component.

Removal is mandatory when one of these conditions is reached:
1. Spring Boot / dependency management resolves embedded Tomcat to **>= 11.0.25**;
2. Apache changes the advisory so non-example embedded deployments are affected;
3. the suppression reaches its hard expiry on **2026-09-08 UTC**.

The security workflow sets `failBuildOnUnusedSuppressionRule=true`. Therefore a dependency upgrade that fixes/removes the finding deliberately turns this suppression into a CI failure until the rule is deleted. Agents must **remove** an unused suppression, not weaken that check. Extending the expiry requires a fresh upstream advisory review and an updated explanation in both `.agents/` and `docs/development/TESTING.md`.

Automated Dependabot version-update pull requests are disabled. The daily NVD/OWASP
scan, frontend `npm audit`, container Trivy scan, and repository security audit remain
the vulnerability boundary. They intentionally do not act as a general dependency
freshness service. Routine Maven/npm upgrades, container runtime changes, and updates
to SHA-pinned GitHub Actions are reviewed maintenance changes and must pass the full
gate; do not reintroduce broad automated major-version PRs as a substitute for that
review.

### 2026-08-08 security/TLS backlog closure

The former `.agents/ToDo.txt` security items are closed as enforced invariants. Test is the default origin target; Production requires `--production`, and the selected runtime receives `DEPLOYMENT_ENVIRONMENT`. Production must use a public hostname, `TLS_MODE=letsencrypt` and `LETSENCRYPT_STAGING=false`; test may use staging/self-signed. Never copy certificates from test to production: each target owns `shared/data/{certs,letsencrypt}` and obtains its own certificate. `sync-certificate.sh` validates hostname, key pairing and remaining lifetime before atomic replacement. Hostname validation fails closed across OpenSSL versions: `x509 -checkhost` must both execute successfully and explicitly report a positive certificate match, because older versions may print a mismatch while returning status 0.

Release PostgreSQL is no longer host-published. Uploads are bounded at gateway, Spring multipart and service quota/type/signature layers. Frontend route guards and upload checks are defense-in-depth only; backend authorization and validation remain authoritative. Update activation still requires coordinated pre-deployment backups and restores the previous release/data on failed activation. Debug API 500s through the stateful HTTP integration suites and SQL runtime audit rather than ad-hoc production container sessions.

### 2026-08-08 deployment-host quality-tool portability

Mandatory `update.sh`/deployment quality gates must not depend on optional developer utilities. In particular, TLS/environment safety checks use baseline `grep` plus `openssl`; `ripgrep` (`rg`) is not a deployment-host prerequisite. If a new mandatory gate needs an external command, either declare/install it explicitly as an infrastructure prerequisite or implement the check with the existing baseline toolset.

### 2026-08-09 production bootstrap and 1-vCPU deployment corrections

Production origin configuration now remains UX-first while keeping secrets target-local:
`./deploy.sh --production --configure` asks for the public DNS name and Let's Encrypt
contact email, and the target creates its fresh private environment and bootstrap
credentials before installation. Subsequent production deploys reuse the target-local
environment. The runtime API starts with Flyway disabled because the one-shot schema
container owns migration execution; the API uses only the restricted database role.
Compose CPU defaults are valid on a 1-vCPU VPS: PostgreSQL and API use quotas of `1.0`.
Larger targets may override those quotas through `POSTGRES_CPU_LIMIT` and
`API_CPU_LIMIT`.

### Server-wide build printout cache

Since v1.0.13, build PNGs are treated as a bounded, shared derived cache.
Identity = renderer version + SHA-256 of the source SVG render; `builds.updated_at`
remains exclusively the business revision. The API returns a versioned
`printout_url?...cache_key=...`; every viewer may read a current hit, while only
owner/staff may create or repair it.

Only the currently selected cache entry remains active for each build. The file is
checksum-versioned, switched transaction-safely, and the previous file is removed
after commit. Update/role change/deletion invalidates the cache. The global storage
cap and minimum free space apply jointly to uploads and printouts; daily cleanup removes
stale metadata, orphans, and temporary files; fresh orphan candidates receive a one-hour
grace window against active cache commits. Whenever a print-renderer change can alter the
visible result, bump `BUILD_PRINT_RENDERER_VERSION` as well. V8 is the first forward
Flyway migration after the immutable modular V3–V7 baseline; SQL audits must not interpret
V8+ as drift relative to V1.
