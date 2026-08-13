## 2026-07-28 - Repository spring clean and security audit
- Discord webhook credentials are now stored as authenticated, versioned ciphertext with automatic plaintext migration and key rotation; deployment setup generates a database-independent key, and decrypted targets are revalidated against the Discord allowlist immediately before delivery.
- Removed the obsolete Discord avatar override from API, service, model and database; all webhook deliveries keep the public fleet icon.
- Added offline repository-specific security invariants plus OSV pull-request, main-branch and weekly dependency scans.
- Hardened GitHub checkout usage, NGINX cross-origin headers, and the read-only migration/seed container posture.
- Added a reviewed Uptime Kuma 1→2 migration runbook instead of applying an unsafe unattended major upgrade.
- Refreshed security, privacy, operations and webhook documentation and removed stale compatibility guidance.

# Changelog

## 1.5.13 - 2026-08-13

- Reworked the New Captain Guide into one Explorer-style knowledge workspace with
  persistent topic navigation, address and status bars, a details list, and an
  integrated long-form preview pane.
- Combined compact Build-library search and content-type filters with native
  briefings and curated Guide, Build, internal-page, and external-link resources.
- Aligned moderator organization and editing with the same ordered folder and
  resource hierarchy members browse, including read-after-save browser coverage.

## 1.5.10 - 2026-08-11

- Centralized the strategy editor and read-only briefing layout in one reusable
  document presentation so on-screen, SVG, and print structures cannot drift.
- Moved browser-only strategy SVG serialization out of the pure domain layer.
- Hardened strategy background publication cleanup by using the explicit joined
  background-file identifier, with mutation regressions for update, sharing, and
  deletion.
- Expanded the repository-agent spring-cleaning guide with a repeatable
  post-feature audit for duplicate flows, dependency direction, joined-row key
  collisions, public-route contracts, persisted files, and regression quality.

## 1.5.9 - 2026-08-11

- Made strategy SVG downloads portable by embedding the authorized background
  image and resolved presentation styles together with the drawing overlay.
- Reworked strategy printing into an A4 landscape briefing/chart page followed
  by a dedicated player, build, and guide page with non-splitting legend entries.
- Documented and regression-tested recovery coverage for strategy database rows,
  catalog references, publication state, and uploaded chart backgrounds.

## 1.5.7 - 2026-08-11

- Added a two-layer Port-Battle strategy planner that preserves uploaded charts
  while keeping scalable and rotatable ship markers, freehand drawings, lines, arrows,
  formations, and text independently editable.
- Added optional player assignments and website-backed build and guide links to
  ship markers, with server-side validation that referenced resources exist.
- Added private strategy storage, revocable read-only share links, SVG export,
  and print/PDF support with privacy, retention, and ownership enforcement.
- Added bounded, loss-aware JPEG/PNG optimization for all persisted uploads and
  derived build printouts, including strategy backgrounds and accurate post-optimization
  quota, size, and checksum accounting.
- Corrected strategy freehand coordinates for responsive and letterboxed canvases,
  and restricted linked builds to the ship represented by each marker in both the
  editor and server-side validation.

## 1.3.6 - 2026-08-10

- Wired maintenance mode into update, rollback, restart, and database restore
  lifecycles so the gateway serves a controlled HTTP 503 page until readiness
  and smoke checks complete.
- Added configurable MAINTENANCE_URL support with a backward-compatible
  /maintenance.html default and documented the remote deployment behavior.


## 1.3.5 - 2026-08-09

- Added the canonical public Royal Blackwater Fleet icon as the fixed Discord
  avatar for automatic webhook events, connectivity tests, manual broadcasts,
  and stored delivery retries.
- Kept avatar configuration out of the browser and webhook records so every
  destination uses the same project-owned identity by default.

## 1.3.4 - 2026-08-09

- Restored event-specific Discord webhook defaults for existing installations by
  removing only the exact legacy generic template override during migration.
- Added an immediate selected-event template preview while keeping the optional
  webhook-wide custom override visibly separate.
- Added migration and frontend regression coverage for both behaviors.

## 1.3.3 - 2026-08-09

- Removed noisy Dependabot version-update pull requests while retaining the daily
  NVD/OWASP, npm audit, Trivy, and repository security gates; routine upgrades are
  now explicitly reviewed maintenance changes.
- Fixed production frontend API configuration by using Vite's statically replaced
  environment access and added a regression test that forbids dynamic access.

## 1.3.2 - 2026-08-09

- Fixed coordinated backup verification on deployment by accepting PostgreSQL's
  supported 63-character identifier limit for generated restore-preflight
  database names.
- Added boundary tests for generated, maximum-length, unsafe, and overlong
  database identifiers.
- Kept restore-preflight staging database names within the historical identifier
  boundary so an incoming release can validate backups through an older active
  schema image before activation.

## 1.3.1 - 2026-08-09

- Promoted the hardened deployment baseline after production beta activation.
- Made production bootstrap interactive from the origin host while generating
  secrets and the private environment only on the target.
- Separated runtime API startup from Flyway bean creation and made Compose CPU
  defaults compatible with 1-vCPU VPS hosts.

## 1.3.0 - 2026-08-09

- Prepared the compatible beta deployment release with the recovery-tool workflow,
  founder fleet role, neutral/game asset switch, dependency safety checks, and the
  Java test-surface generic compatibility fixes included in the release baseline.

### Fixed

- Repaired the fleet-management API contract: Java keyword-backed DTO fields now retain their OpenAPI wire names, fleet-role routes validate their fleet scope and management authorization, and first-run/integration smoke coverage exercises the complete manageable-fleet → management-detail → roles request chain.
- Made Spring `@Repository` beans and shared JDBC repository methods CGLIB-proxyable after the real Spring Boot/Testcontainers integration run exposed final-class proxy failures.
- Replaced deprecated Spring 7 `HttpStatus.UNPROCESSABLE_ENTITY` usages with `UNPROCESSABLE_CONTENT`.
- Scoped MapStruct annotation-processor compiler options to main compilation to avoid false test-compile processor warnings.

## Unreleased

- Reintroduced the recovery client after the Spring Boot migration as a focused
  target-aware tool. Test and production profiles are isolated, setup imports
  the public enrollment response while retaining private recovery material
  locally, and pulls require the current Spring/Flyway preflight plus the exact
  release artifact before a bundle is accepted. Added Linux/Windows packaging
  wrappers and CI coverage for the client protocol.

## 1.2.0 - 2026-08-09

- Raised the deployable application release to 1.2.0 across Maven, frontend metadata and the OpenAPI contract. The `patches/` directory remains available as a local transfer/download workspace, while patch payloads are ignored by Git so release history stays in commits and the changelog instead of duplicated patch archives.



- Expanded the post-Surefire JaCoCo pass with authenticated controller execution, empty/populated business dependency matrices, type-aware populated synthetic rows/collections/optionals, transaction cleanup-hook coverage, and an isolated application-bootstrap delegation test; coverage thresholds remain unchanged and must be satisfied by additional executed production paths rather than by lowering release gates.
- Repaired the first full Maven backend-test pass after the go-live coverage expansion: synthetic surface tests now build type-correct nested generic/record values and neutral collaborator returns instead of producing harness-only `NullPointerException`/`ClassCastException` failures, resource-backed binary DTOs are no longer forced through JSON serialization, and the Build-service bulk-ID regression uses a null-tolerant input list. The run also exposed and fixed real numeric-normalization defects in Build effect/stat/catalog handling so mathematically integral values remain `Long` rather than being silently retained as `Double`; dynamic specialist effects are normalized before their first map insertion as well as during later merges, while genuinely fractional values remain `Double`.
- Expanded and independently hardened the Spring backend go-live test strategy so every production class belongs to exactly one enforced test strategy and every production module has module-local coverage. Every discovered business component now requires a module-local focused semantic test in addition to the recursive executable public-entry-point safety net; controllers, repositories, mappers, configuration, persistence/shared helpers, filters, generated/module DTOs, entities and SQL catalogs each have explicit executable or structural contracts. The complete OpenAPI surface retains anonymous/CSRF boundary coverage, and Maven verification fails below 80% line, 65% branch, 80% method or 60% per-package line coverage with no completely missed analyzed production class. JaCoCo exclusions remain restricted to generator-owned root OpenAPI DTOs and static SQL catalogs so executable entity/module-DTO logic cannot disappear behind broad exclusions.
- Hardened TLS certificate hostname validation across OpenSSL versions that may print a mismatch while still returning success; certificate activation now fails closed unless `openssl x509 -checkhost` explicitly reports a positive hostname match, with a regression test for the legacy exit-status behavior.
- Added correlation-first API diagnostics: every API response receives `X-Request-Id`, central error/security records carry the same ID, and opt-in payload-free request lifecycle logging exposes normalized route, status and duration for automated tests and short debugging windows.
- Expanded Build printout cache regression coverage across Flyway V1-to-current upgrades, fresh V8 schema application, service-level cache reuse/invalidation and a real HTTP/PostgreSQL/filesystem lifecycle; migration compatibility tests now derive pending migration counts instead of hard-coding them.
- Split hand-maintained OpenAPI operations/schemas, Build stat definitions, Build option seeds and ship-rate seeds into responsibility-scoped JSON files while retaining deterministic generated compatibility artifacts and stable catalog order; the repository gate now caps hand-maintained JSON at 420 lines.

- Reconciled the Spring HTTP error contract and bootstrap-login lifecycle: generated request DTOs and login bindings remain unchanged, validation errors now use HTTP 400 with the shared `ApiError.detail` shape, semantic 422 responses are explicit, login documents invalid credentials as 401, and genuinely fresh installations verify generated bootstrap credentials through the public login API without ever resetting an existing administrator password. The post-cutover release baseline is reset to 1.0.0.

- Hardened the post-refactor Spring API type boundary: fixed missing mapper imports, corrected the privacy export category generic type, repaired the Raid-Helper probe result mapping, removed the remaining unused import, replaced all residual Java wildcard imports with explicit imports, added serialization metadata to custom exception types, and extended the Spring audit to reject wildcard, duplicate, unused, unresolved and commonly missing project-internal imports. Architecture, API, development and debugging documentation now reflect the controller/service/mapper/repository design instead of the retired handler flow.
- Cleaned the Spring API package tree: removed all ambiguous `model` packages, moved internal transition records into module DTO packages, placed seed/event catalogs in their owning repository/service layers, removed an unused Spring Data repository and dead controller helpers, and replaced Map-based query-parameter roundtrips with typed filters. Architecture gates now reject empty source directories, generic model packages, raw controller parameter maps and repositories without consumers, and the repository cleanup script now removes generated file artifacts without the conflicting `find -prune`/`-delete` combination.
- Completed the DTO boundary refactor across the Spring API: 179 generated request/response records now match the OpenAPI contract, all 177 operations use concrete response types, every HTTP module owns mapper-based transitions, and architecture gates reject entity/raw-row exposure, wildcard responses, controller body recasting and API-DTO construction outside mappers.
- Completed the Spring Boot cutover: all 177 API operations are native, the FastAPI/Python runtime and catch-all proxy are removed, Flyway and versioned Java seeding own database lifecycle, and deployment/update/backup/restore now consume immutable compiled release artifacts instead of a source checkout.
- Added bounded shared list filters, strict numeric conversion and server-side caps for unpaginated discovery endpoints. Batched guide owners and build references, master-data ship relations, squad and newcomer-guide collections, and request-local build catalogs remove the reviewed N+1 read paths; focused tests and repository invariants guard the optimizations.
- Added Java 21 syntax parsing to local validation and a PostgreSQL Testcontainers application-start test covering Flyway, reference-data seeding and bootstrap-administrator creation.

- Reconciled and simplified the backup-server enrollment module end to end for Recovery Tool 1.4.2. The Staff UI now provides a four-step setup wizard, exact copy-and-paste provisioning commands, visible file validation and progress, and keeps manual private-key entry collapsed as an advanced fallback. The API validates the complete response synchronously, the host runner preserves failed responses for retry and retains transactional live host-key/SFTP roundtrip checks, and the Linux provisioner enforces the requested account and `/data` contract with actionable errors and numbered next steps. A concise quickstart and troubleshooting runbook documents the same workflow for future operators.

- Added an assisted backup-server enrollment workflow. The protected product host now generates its own dedicated SSH key and a public enrollment request; the Linux Recovery Tool 1.4.0 provisions separate chrooted key-only upload and loopback-only read-only recovery SFTP accounts, storage directory, OpenSSH policy, age identity, local recovery key/profile, retention timer and optional source-address firewall rule on the backup server. A public response file is imported in Staff, live host-key pinning and SFTP are verified automatically, encrypted recovery backups are enabled without transferring private keys, and scheduled backup sets are now automatically published offsite with the set manifest last as the remote commit marker.

- Hardened backup and recovery as separate production contracts. Coordinated backup runs now quiesce the API when necessary, create PostgreSQL and runtime-file artifacts at one application boundary, restore the fresh dump into staging, migrate it to the current Alembic head, verify encryption keys and API readiness, and commit the set only through a checksummed manifest that binds the artifacts to a successful recovery report. Production restores and the desktop recovery client share migration-compatibility semantics, distinguish import-only checks from full recoverability, support fail-closed preflight-only operation, and CI exercises a historical-schema dump/restore/migration/readiness matrix. The recovery-tool package version was 1.3.0 for that milestone.

- Fixed recovery-lab Compose generation: the PostgreSQL healthcheck now uses a YAML block sequence with safely nested shell quoting, generated files are parsed in a regression test, and recovery-tool tests now run in both local validation and CI. The recovery-tool package version is now 1.2.1.

- Fixed and hardened recovery-tool packaging: Linux DEB builds now depend on `pkexec` instead of the obsolete `policykit-1` transition package, all checksum sidecars use portable basenames, every Linux/Windows build clears generated output before prerequisite validation so failed rebuilds cannot expose stale packages, standalone DEB/installer builders remove their old outputs before validating input, and repository/CI gates reject regressions, compiled packages, build environments, generated locales and sensitive local files.

- Expanded the frozen Linux recovery client into a one-command user installation with an optional systemd pull timer and an opt-in rootless-Docker PostgreSQL recovery lab. The lab binds only to loopback, preserves random credentials in a mode-0600 user file, uses the production PostgreSQL image line, verifies the complete encrypted bundle before extracting the database artifact, and supports one-click restore tests without granting docker-group root privileges. An official-repository Ubuntu provisioner, native CLI modes and a portable installer archive are included.

- Hardened PostgreSQL and disaster recovery after a real bare-metal restore exercise: database restores now import into an isolated staging database while production remains available, migrate and validate encrypted webhook/Raid-Helper credentials before activation, switch databases atomically, and automatically roll back to the previous database if API readiness or HTTPS smoke checks fail. PostgreSQL backups now include checksummed restore metadata with Alembic and encryption-key fingerprints; the Staff catalog blocks known-incompatible key rings, legacy backups receive an authoritative staging preflight, full recovery bundles verify the saved `.env` key ring, and an audited host tool can merge old key material without printing secrets. Optional integration credentials can no longer prevent the API from starting; undecryptable webhooks are disabled for administrator repair instead.

- Added one shared frozen recovery client for Windows and Linux with pinned SSH host keys, embedded native age tools, SFTP pull, atomic downloads and full encrypted-bundle verification. Native PyInstaller wrappers produce a Windows EXE or architecture-specific Linux binary from the same reviewed source. The Staff backup panel can catalog checksum-verified local PostgreSQL dumps and perform a bootstrap-admin-only restore after a short-lived, single-use approval generated with sudo on the host; browser input can never select arbitrary filesystem paths, and plaintext approval tokens are never queued.

- Added production-grade Raspberry Pi disaster recovery: scheduled backups can now create one age-encrypted bundle containing PostgreSQL, uploads, TLS/Let's Encrypt, Uptime Kuma, `.env`, all `.cfg` snapshots, root-side backup secrets and a per-file SHA-256 manifest. A pull-only export supports Windows OpenSSH clients without exposing plaintext secrets; PowerShell key generation, pull and full-content verification scripts plus an automated bare-metal restore workflow are included.

- Added the newly supplied owned-ship audit data for Sparrow, Black Wind and Prins Willem. Their verified cruise maxima and sparse ship-specific upgrade values now replace shipyard placeholders; Black Wind's dedicated mortar-fitting panel is recorded as direct evidence. The screenshot audit and integrity manifest now cover 254 ship captures across 41 owned ships.

- Split Raid-Helper payloads into a free-compatible default and an explicit Premium opt-in. Standard templates now send only the proven basic create-event fields, while custom template IDs and additional top-level kwargs require `uses_premium_features`; invalid free-mode templates are rejected locally before any API request. Migration `0020` converts the former application-recommended payload to the free-compatible preset and preserves intentional custom payloads as Premium templates.

- Fixed the remaining Raid-Helper 401 false positive by making destination tests render the same selected application template and JSON payload as calendar delivery. Raid-Helper template IDs are now optional, the legacy application default `Standard` is omitted instead of sent as `templateId`, and the Staff panel can compare a selected template payload against a minimal payload. Migration `0019` clears legacy `Standard` values and changes the database default to an empty template ID.

- Replaced the misleading Raid-Helper profile “connection” result with an explicitly read-only server check and added an exact destination write test that creates and immediately removes a temporary event using the same API key, server, channel, leader and endpoints as calendar synchronization. Calendar status now identifies the profile behind each destination, copied key wrappers are normalized, and event dates use Raid-Helper's `DD.MM.YYYY` format.

- Fixed Raid-Helper HTTP 401 responses by removing the misleading Bearer/X-API-Key options and always sending the decrypted API key as the raw `Authorization` header required by the v4 server API. Migration `0018` removes the obsolete profile authorization-mode column.

- Added required Raid-Helper leader assignment: profiles can store a default Discord leader user ID, event managers can persist a manual override per selected appointment destination, and the validated effective value is resolved at delivery time and injected as `leaderId` into every create/update payload, including custom JSON templates. Migration `0017` adds the profile default and per-event override columns.
- Fixed Raid-Helper event creation against the documented v4 API: profiles now use and migrate to `raid-helper.xyz`, exact JSON placeholders preserve identifier types, and bounded top-level API validation messages are shown to event managers instead of a bare HTTP status. Failed deliveries now expose an explicit manager-only retry action. New templates use the free-compatible basic payload by default; advanced time-display, signup, custom-template and other additional kwargs are available only through the explicit Premium opt-in.
- Refactored the global CSS cascade around explicit layer ownership: removed retired navigation/footer selectors, consolidated exact duplicate rules, normalized responsive webhook and operation layouts, and strengthened the CSS audit against shell ownership regressions. The application footer is now owned by the shell layer, aligns with the main workspace beside the desktop sidebar, follows long content, and stays at the viewport bottom on short pages across desktop, tablet, and mobile layouts.
- Added a controlled administrator-only application restart operation to the Staff status panel. The root-side runner restarts the API and gateway in order, keeps PostgreSQL online, waits for readiness, runs smoke checks, and returns only privacy-minimal state to the website while detailed results remain in host logs and configured webhooks.
- Restricted administrator delegation to the configured bootstrap administrator: it may promote users to administrator and demote promoted administrators, while non-bootstrap administrators cannot promote or demote administrators. Migration `0015` selects an existing active administrator during upgrades, and normal seeding reconciles the capability with the configured default account.
- Reworked upload publication so client-supplied usage context no longer makes guide or forum files public. Files remain private until linked to published server-authorized content; master-data uploads require an administrator and explicit public visibility is persisted.
- Added paginated lightweight build collection responses, preserving full calculated statistics for detail views while bounding list payload and CPU cost.
- Extended remote administration backups to create, checksum, transfer and remotely verify both PostgreSQL and file-data archives, including uploads and optional certificate/Uptime Kuma data.
- Removed requester identities, commit hashes and log tails from the website update-status API and UI; detailed diagnostics remain in host logs and webhook notifications.
- Limited Raid-Helper duplicate-name handling to integrity violations while rolling back and re-raising unexpected database failures.
- Added a full-stack Chromium smoke workflow covering registration approval, login, privacy-minimal update status, and paginated build access.

- Fixed the Raid-Helper production startup failure by replacing the accidental development-only `httpx` dependency with the existing hardened outbound HTTP transport. Raid-Helper requests now reuse DNS pinning, public-address validation, TLS hostname verification and redirect blocking without adding a new runtime package.
- Added an admin-only Raid-Helper v4 calendar integration with multiple encrypted server profiles, fleet- and squad-specific channel destinations, category-filtered templates, default-on per-event delivery, create/update/cancel synchronization and visible per-target delivery status for event managers. Existing calendar webhook messages now expose normalized fleet/squad scope fields, and the Staff template editor includes matching fleet/squad presets. Migration `0014` creates the normalized profile, destination, template and event-link tables without requiring a seed.
- Added crawler load protection for the Raspberry Pi deployment: a restrictive `robots.txt`, explicit denial of declared high-volume AI training crawlers, separate per-IP limits for public pages and API traffic, connection limits, and `X-Robots-Tag` on API and authenticated workspaces.
- Fixed the Impressum administration workflow: the `.env` reset action now rereads the configured environment source instead of using only the startup cache, the default English UI consistently labels the page “Impressum”, and the application shell keeps the footer at the bottom of short pages without a viewport overlay.
- Added a public, draft-capable German legal-notice page at `/impressum` and an admin-only editor in the Staff workspace. Environment variables provide deployment defaults, while persisted administrator changes take precedence and survive updates; admins can explicitly reset the record to the currently loaded environment values. Migration `0013` creates the normalized singleton record without requiring a seed.
- Added a member-only, data-driven Combat DPM Analysis module with independent armor targets for one broadside, side-switching across both broadsides, bow and stern. Weapon damage/reload inputs now live in normalized `weapon_performance_profiles` master data, the initial 21 broadside profiles come from the supplied cannon comparison, Staff can maintain verified profiles, and missing bow/stern values are reported instead of estimated. Migration `0012` backfills existing cannon options.
- Corrected bow/stern weapon sizing: standard positional weapons now use the same normalized Light/Medium/Heavy mount ceiling as broadside cannons. Rate-7/6/5 mounts only expose Light positional weapons, Rate-4/3 mounts expose Light and Medium, and Rate-2/1 mounts expose all three classes. Friede therefore no longer receives the entire bow/stern catalogue, while the audited compatibility examples remain valid (Eagle: Basilisk/Poseidon; Azov/Deadfish: Zeus). Migration `0011` assigns the normalized weapon classes; no per-ship exceptions are introduced.
- Removed the mistaken per-ship bow/stern allowance table in migration `0010`. Positional weapons remain linked to normalized bow/rear slot types; migration `0011` adds the required Light/Medium/Heavy ceiling so availability is determined by both slot position and mount class.
- Reworked frontend stacking into one semantic z-index scale and moved Build Planner option menus into a body-level fixed popover portal. Ship, Specialist, equipment and inventory pickers now stay above the shell and every planner stacking context, reposition on viewport scroll/resize, flip above the trigger near the viewport edge, and remain below mobile drawers and modal Staff editors. Added regression checks that reject local numeric z-index values.
- Added a searchable ship picker to the Build Planner. Ship name, type and rate are filtered immediately against the already loaded ship catalog, so typing never triggers additional API requests; selection, keyboard navigation and empty-result handling reuse the existing accessible option picker.
- Corrected the Build Planner upgrade add-on to grant one data-driven upgrade slot while applying `-5%` durability, maneuverability and cargo hold. The feature and its individual effects now live in normalized database tables and Builds store only the selected feature reference. Added normalized rate-to-weapon-class rules so newly created ships receive Light weapons for rates 7–5, Medium for rates 4–3 and Heavy for rates 2–1; migration `0008` also repairs previously stored, classless regular mounts without overwriting explicit audited exceptions or touching mortar/special mounts.
- Added one-shot recovery for stale lazy-loaded frontend chunks after a server update: failed route imports now reload the requested route against the new deployment, while a per-route session guard prevents reload loops.
- Added normalized one-vote-per-user Build upvotes with vote totals in Build lists, personal lists and details; introduced moderator-managed Build-role CRUD and direct role assignment in the Staff workspace; added an in-memory Specialist picker search, corrected Build Planner dropdown stacking, and published configurable `system.update.started` / `system.update.result` webhooks with retry-safe result deduplication.
- Replaced persistent request logs with an admin-only IP-ban signal store: only the normalized IP, UTC calendar day, one coarse signal category and a daily counter are retained for seven days. Routes, query strings, user agents, request IDs, payloads, exact timestamps, status details and exceptions are no longer persisted or exposed in the Staff UI; old `app_logs` data is deliberately discarded by migration `0006`, signals are deleted as soon as an IP is blocked, client-supplied request IDs are ignored, and gateway access logs remain disabled.
- Fixed Build Print icon rendering in preview, SVG, PNG and print output by binding the browser fetch receiver correctly, embedding catalog assets before the generated SVG is used as an image, and falling back to same-origin image/canvas rasterization when direct response conversion is unavailable. Failed embedding no longer silently produces broken image placeholders. Upgrade, sail, lantern, specialist and inventory entries now use their selected catalog images without relying on external SVG resource loading.
- Discord event webhooks and manual broadcasts now always use the bundled Royal Blackwater Fleet icon. Custom avatar controls were removed from the Staff UI and legacy avatar values can no longer override the server-side payload.
- Corrected First Mate semantics: `+0.2% per Sailor` now increases sail deployment speed only, appears as its own calculated stat, and can no longer inflate base or cruise ship speed. Added the 102-Sailor Zeven regression (`14.7 kn` ship speed and `+20.4%` sail deployment speed).
- Fixed master-data seed recovery: individual restore actions are real buttons, admins can reset all repository-owned categories, options and ships from the master-data workspace, and custom records/user content remain untouched. Added `update.sh --restore-seed-defaults` for the equivalent audited server-side repair flow and explicit reporting when normal seeds preserve admin overrides.
- Completed the selectable ammunition seed catalog with Heavy Shots and Saxon Shots, stable seed IDs and translations in every supported locale.
- Audited Build Designer arithmetic end to end: De Zeven Provincien plus Raiding Sails is fixed at the verified `14.7 kn`, percentage/flat components remain dimensionally correct, and all Python/JavaScript crew and specialist rounding now uses one decimal half-up contract.
- Added a shared calculation contract and coverage gate for all 106 numeric seed-effect keys.
- Added Discord website-webhook events and versioned templates for group-search creation, joins and closure; fleet-scoped delivery follows the listing owner and payloads omit contact/member notes.

- Fixed a deployment deadlock where seed or migration updates invoked `backup-all.sh` while already holding `update.lock`; update backups now reuse the existing update lock and acquire only `backup.lock`.

### Owned-ship seed audit

- Re-audited 38 owned ships from 230 current in-game screenshots, adding 12 Apostolov, Balloon, Flying Cloud, Huracan and La Royale to the prior owned batch and updating their displayed cruise-speed maxima.
- Added sparse screenshot-backed upgrade values for 28 ships, including the newly verified 12 Apostolov, Flying Cloud, Huracan and La Royale combat exceptions while preserving inherited global effects for all unlisted values.
- Ship master-data edits now synchronize existing sparse upgrade rows in place, preventing uniqueness conflicts when administrators edit ships that already have seeded overrides.
- Corrected the global Teak Frames armor value from `15` to `1.5`.
- Extended the JSON seed schema and bootstrap so ship-specific upgrade values resolve by stable upgrade IDs, survive normal reseeds and are restored by the master-data admin workflow.
- Documented account-level upgrade-slot handling and retained ambiguous mortar layouts until quantified modification panels are available.
- Corrected Balloon to zero upgrade slots from its explicit `Upgrades -` panel and prevented research or expansion effects from creating a rack on rackless ships.

### Repository spring clean and privacy hardening

- Split the historical 11,466-line global stylesheet into eight deterministic JavaScript-imported cascade layers with budgets and a standalone CSS audit.
- Reused one presentational filter surface across the staff workspace and documented KISS/SOLID boundaries.
- Replaced nested full user profiles with minimal identity references in shared content APIs.
- Redacted reviewed registration password hashes and all request query values.
- Added configurable retention for webhook deliveries, cookie consent history, and registration requests.
- Added a security/privacy audit and operational data-retention documentation.
- Split webhook event metadata, samples, and templates behind a thin compatibility facade.
- Made the locale completeness check directly executable with Node instead of requiring a Vite server.
- Pinned GitHub workflows to the published v6 releases of checkout, setup-node, setup-python, and upload-artifact.

- Added admin-only database backup management: configure an SSH/SFTP target through the website with verified host-key pinning, test the connection, transfer compressed PostgreSQL backups at the push of a button, and verify them remotely with SHA-256. Private keys remain in the root-protected host-control directory and are never returned by the API.
- Repaired the frontend release gate: added complete translations for the new broadcast navigation and adjusted route-page invariants for the backup subpage; moved GitHub Actions back to published, runner-compatible major versions.
- Split Discord administration by responsibility: automatic website webhooks remain under “Discord Webhooks”, while external partner-fleet and diplomacy targets have their own broadcast subpage; the delivery monitor is collapsed by default and its history can be deleted individually or by filter.
- Forum replies can be deleted after inline confirmation by the author or staff; new webhook events and versioned templates cover replies, thread deletions, and fleet, membership, leadership, and role changes.
- Moved staff system logs into their own responsive workspace; active IP blocks are excluded from the list, metrics, and threat analysis by default and can be deliberately shown again. Admins can delete individual entries or the current filtered range after confirmation; every deletion remains traceable in the audit log.
- Migrated all route pages to mandatory page composables; direct API imports, lifecycle loading, and custom asynchronous workflows in pages are now prevented repository-wide.
- Split global frontend CSS into eight size-bounded layers while preserving cascade order and enforcing CSS budgets.
- Pinned Python, Node, NGINX, PostgreSQL, and Uptime Kuma base images to concrete versions; removed the unversioned pip self-upgrade from the backend build.
- Hardened upload delivery with API access policy and private no-store headers: guide, forum, and master-data files remain public, while other files are restricted to owners and staff; existing `/uploads/...` links remain compatible.
- Added a protected delete action for users' own builds to the Build Editor; after confirmation, the build is removed and navigation returns to the personal build library.
- Implemented the Discord webhook editor as an isolated, responsive body drawer; checkboxes, form controls, and actions no longer overlap, and the background is locked while editing.
- Made webhook deliveries claimable atomically and added automatic recovery of orphaned `queued`/`processing` entries with bounded attempts.
- Production logging now emits structured messages to the console as well, so database failures do not disable runtime diagnostics at the same time.
- Hardened release checks against platform-dependent line endings and a stale Alembic head; corrected several fixtures whose behavior depended on test order.
- Original upload filenames are truncated to the database boundary before persistence.
- Webhook template autofill and backend default messages now use the complete English repository templates exactly, including context fields and deep links; a release invariant prevents renewed drift.
- Repaired the staff overview with its own responsive dashboard layout; metrics, queues, and administrator notices remain clearly separated on desktop, tablet, and mobile.
- Extended the Discord webhook editor with template autofill from the versioned event catalog and a compact, searchable multi-select for subscribed events.
- Extended Discord chat webhooks with independent multi-channel subscriptions and a manual broadcast panel; broadcast-only targets, multi-selection, dedicated delivery history, and retry are supported directly by the backend.
- Retained Discord channel webhooks as the only Discord integration; cleaned staff navigation, API, and infrastructure around direct backend delivery.
- Consolidated the Alembic schema for the intended clean setup into a current `0001_baseline`.
- Gateway builds now normalize frontend directory permissions to `0755` and file permissions to `0644`, ensuring bundled assets such as `rbf-fleet-icon.png` remain publicly readable.



## 2026-07-28 - Default discovery results and CSS cascade restoration

- Loads all builds and all published guides immediately when their library pages open.
- Clearing filters now returns to the complete result set instead of hiding the result panel.
- Restores the shared CSS to one deterministic stylesheet to match the pre-refactor cascade and prevent production layout drift.
- Adds repository and frontend regression checks for default discovery loading and CSS delivery order.

## 1.0.0 — Production baseline

### Fixed

- Real Build CRUD events now serialize the public `BuildRead` schema instead of a SQLAlchemy object, so `build.created`, `build.updated`, and `build.removed` are scheduled and delivered reliably.
- Unified Fleet/Squad scope metadata for registrations, calendar, builds, guides, forum, and New Captain Guide so real events reach the same subscriptions as intended.
- Event-specific test deliveries use realistic payloads; repository checks enforce exactly one publisher, one serializable test payload, and valid template fields for every event.
- Unexpected errors in webhook background tasks are persisted as failed deliveries instead of leaving entries permanently in `queued` status.
- Expanded English webhook message templates with complete resource data and clickable deep links; webhook envelopes now qualify relative resource paths against the public website origin.
- Notifications for deleted builds and guides link to their still-accessible overview pages.
- Corrected Alembic head detection in the built API image: schema checks now explicitly use `/app/alembic.ini` instead of a nonexistent path in the installed Python package.
- Added directly copyable, versioned message templates for all supported webhook events under `docs/integrations/webhook-templates/message-templates/`.
- Corrected default messages for Build webhooks to use the actual `data.build_name` field.
- Reworked update detection from Git diffs to a runtime comparison between the Alembic head of the newly built API image and the actual PostgreSQL revision; failed migrations are safely detected again on the next run.
- Admin update requests are accepted only after acquiring the exclusive lock; parallel runners no longer lose requests or overwrite an active status.
- Added update heartbeat and recovery for orphaned `queued`/`running` states; interrupted host runs no longer block new requests indefinitely.
- `--seed` now always implies `--migrate`; `--no-auto-migrate` aborts before API deployment when the schema differs.
- Running API and gateway image IDs are captured as the exact rollback point and preferred over a non-reproducible rebuild.
- Extended PostgreSQL restore with an exclusive lock, pre-restore backup, maintenance mode, connection termination, Alembic upgrade, and readiness/smoke checks.
- Corrected backup counters in the doctor script to use the actual subdirectories and protected backend test modules with process-group timeouts.

- Shortened the Alembic revision ID for registration fleet applications to PostgreSQL-compatible 26 characters and added a 32-character repository invariant.
- Adapted repository and infrastructure checks to the modular setup/update runners and `.cfg` configuration.
- Added a frontend-backend contract test that validates API paths and shared domain values against OpenAPI and backend rules.
- Removed the stale internal registry reference from the frontend lockfile and synchronized fleet focus values between frontend and backend.
- DNS/transport errors from outgoing webhooks now provide a concrete diagnosis for the actual Compose service `api`.
- Extended staff system logs with a day filter, sortable IP overview, and heuristic threat-level dashboard.
- Added audit history for builds, forum threads/posts, guides, and the Starter Guide.
- Standardized the in-game weapon-layout convention to stern–broadside–bow, correcting swapped bow/stern capacities across the catalog.
- Long Build notes are rendered completely in the offline Build image with dynamic page height.
- Extended Build Manager with ship previews, crew-role images, and category-specific image placeholders; master-data images remain uploadable.
- Modeled ship speeds as separate base and cruise maximum values; percentage and flat bonuses use the verified in-game formula.

- Expanded Build Designer to up to eight upgrade slots: 4 standard + 1 research reward + 2 from Structural Expansion + 1 ship-specific extra slot
- Re-audited the upgrade catalog to 32 current in-game upgrades across Speed, Expedition, Protection, Combat, Unusual, and Mortar categories
- Retained global upgrade values as defaults; ship-specific sparse overrides remain editable for every individual ship master-data record
- Grouped upgrade selection in Build Designer by in-game category
- Hid successful `/api/health` and `/api/health/ready` probes from system and NGINX access logs; failed checks remain visible
- Extended the system-log view with a server-side IP filter including filtered metrics
- Added ship-specific upgrade effect values as maintainable sparse overrides in the API, data model, and master-data administration
- Build Designer and server-side Build calculation automatically use the upgrade values of the selected ship
- Standardized specialists to exactly one entry per type; removed quantity counters and stackable effects
- Implemented sailor count as a minimum requirement rather than an upper bound and made save blockers transparent
- Added a “Share Build” action for copying public Build links
- Fixed HTTP 500 errors in staff API logs through a schema repair migration and robust aggregate queries
- Updated the Build Designer ship catalog to 67 records, including the event ship Leopard
- Added Ice Lantern with +5% speed, cargo capacity, and durability
- Re-audited De Zeven Provincien and Sovereign against current in-game panels
- Verified all 67 ship master-data records using in-game screenshots or event tooltips
- Finalized corrections for La Creole, Black Wind, Russia, San Martin, and Le Requin
- Split the main Vite chunk with Rolldown code splitting to below the warning threshold
- Modularized ship seeds by rate and protected them with shared factory/quality rules
- Reworked master-data administration visually and responsively into a catalog workspace
- Unified the upgrade-slot limit across API, database, and Build Designer at a maximum of eight
- Stable FastAPI/Vue module structure and PostgreSQL/Alembic production path
- Removed sample builds, guides, forum posts, groups, events, and demo files from production seeds
- v1 data migration removes known unchanged 0.x mock data while preserving user-created content
- Split Seed Manager by system, ship, and Build-option responsibility
- Added a small Node unit-test base for Build calculation, crew, preferences, and dates
- Isolated backend test runner and tested pre-v1→v1 data-migration path
- Normalized role, fleet, profile, squad, and Build Designer data
- Idempotent, versioned master-data seeds with protected admin overrides
- Complete master-data administration, Markdown content, and editing workflows
- Build Designer with verified sail, lantern, specialist, and weapon rules
- Cookie consent history and cleaned public assets
- Raspberry Pi setup, TLS, firewall, systemd, backups, and diagnostic tooling
- Consolidated v1.0 documentation; removed historical interim-state documents
- Separate GitHub CI jobs, reproducible release artifacts, Dependabot, and optional CD
- Central UTC time source without deprecated `datetime.utcnow()` usage
- Extracted large responsibility blocks from Build statistics, Build form, and system operations

Earlier 0.x states were internal development states and are no longer documented separately from v1.0 onward.
The production schema is consolidated in `0001_baseline` and designed for a fresh clean setup.
Historical development databases are not carried forward through in-place migration.

- Secured Build persistence as a strictly reference-based 3NF model: final values are never stored, and old Builds are recalculated from current ship/option references on every read.
- A repository invariant and integration test now prevent calculated result fields or Build snapshots from being stored in the database.
## 1.0.0

- New Captain Guide supports linked guides and builds.

## 2026-07-28 — Build Designer option visuals

- Added screenshot-derived icons for all 32 ship upgrades and all 51 specialists.
- Added distinct sail and lantern visuals plus additional-sail consumable icons.
- Replaced the equipment and specialist native selects with an accessible,
  icon-aware picker that shows localized effect values directly in the menu.
- Added seed/asset consistency tests and documented icon provenance.
