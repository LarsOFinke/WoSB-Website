# Module Catalog

This catalog is the functional navigation source for all runtime and tooling modules.
It describes responsibility, important boundaries, and the shortest diagnostic entry point.
Individual classes and endpoints remain authoritative in source code and in the
[API reference](../reference/API.md); this catalog does not replace detailed analysis
of the affected flow.

New directories below the three cataloged module roots must be added here and to the
[agent module cache](../../.agents/MODULE_CACHE.md). The documentation gate automatically
compares both inventories with the file system.

## Backend modules

All backend modules live under `spring-api/src/main/java/eu/royalblackwater/api/`.
The normal flow is OpenAPI specification → generated API DTO → module controller →
service → repository/mapper → API/module DTO. For API failures, trace route/`operationId`,
controller, service, and the server-side permission decision together first. Spring MVC
bindings live directly in the controller and are audited against OpenAPI.

| Module | Responsibility and boundaries | Diagnostics and central tests |
| --- | --- | --- |
| `spring-api/src/main/java/eu/royalblackwater/api/account/` | Login, sessions, profiles, registration, user management, and bootstrap admin. Passwords and session tokens never leave the security boundary. | `AuthService`, `BootstrapAdministratorInitializer`, `ApplicationIntegrationTest`; for 401, inspect `security_401` and session/role fetch first. |
| `spring-api/src/main/java/eu/royalblackwater/api/audit/` | Data-minimized history of administrative changes. Audit text contains no payloads, secrets, or full IP addresses. | `AuditService`, `AuditLogQueryService`; inspect entity type, actor, and changed field names. |
| `spring-api/src/main/java/eu/royalblackwater/api/builds/` | Build catalog, validation, calculation, roles, votes, and print output. Calculation and persistence remain separated. | `BuildStatCalculatorTest`, contract fixtures, and build API regressions; for 500, inspect mapper and catalog snapshots. |
| `spring-api/src/main/java/eu/royalblackwater/api/calendar/` | Fleet/squad calendar and event access; Raid Helper delivery remains a downstream integration. | `CalendarService`; inspect ISO `date`/`date-time` binding and `MethodArgumentTypeMismatchException`. |
| `spring-api/src/main/java/eu/royalblackwater/api/config/` | Spring composition, typed configuration, security and error boundaries, scheduling. No business logic. | `application.yml`, `SecurityConfiguration`, `ApiExceptionHandler`; inspect startup binding failures and central `api_error` lines. |
| `spring-api/src/main/java/eu/royalblackwater/api/content/` | Shared validation of safely embedded content. | `ContentEmbedValidator` and calling guide/forum services; test rejected schemes and hosts directly. |
| `spring-api/src/main/java/eu/royalblackwater/api/dto/` | Generated request/response DTOs for the HTTP contract. Domain-internal transfer DTOs live separately under `<domain>/dto`. | DTO generator, contract schema, and DTO boundary checks in the Spring audit. |
| `spring-api/src/main/java/eu/royalblackwater/api/core/` | Small cross-domain core operations such as health/readiness, separated into controller, service, and repository. | `CoreController`, `CoreService`, and `/api/health*`; for readiness also inspect DB and Flyway. |
| `spring-api/src/main/java/eu/royalblackwater/api/files/` | Uploads, content retrieval, quotas, type and ownership checks. Validated JPEG/PNG assets are centrally bounded and loss-aware optimized before metadata is committed; binary data remains in configured storage. | `FileAssetService`, `ImageAssetOptimizer`, storage configuration, and upload boundary tests; inspect path normalization, decode limits, and free space. |
| `spring-api/src/main/java/eu/royalblackwater/api/fleet/` | Fleets, roles, memberships, leadership, and server-side capabilities. Bootstrap fleet leadership is guaranteed by account initialization. | `FleetAccessPolicyTest`, `BootstrapAdministratorInitializerTest`, HTTP squad test; inspect role code, status, and fleet ID together. |
| `spring-api/src/main/java/eu/royalblackwater/api/forum/` | Threads, posts, attachments, ownership, and moderation operations. | `ForumService` and frontend forum tests; for deletion inspect references and permissions separately. |
| `spring-api/src/main/java/eu/royalblackwater/api/groups/` | User groups, memberships, roles, and join flows outside the official fleet. | `GroupService`, group composables, and real user references. |
| `spring-api/src/main/java/eu/royalblackwater/api/guides/` | Guide creation, presentation, attachments, build references, and administration. | `GuideService`, Markdown/print tests; inspect rich-text sanitizing and ownership. |
| `spring-api/src/main/java/eu/royalblackwater/api/legal/` | Publishable legal notice and administrative draft from typed configuration/persistence, including the maintained public-repository transparency reference. | `LegalNoticeService`, `docs/reference/LEGAL_NOTICE.md`; test public and admin views separately. |
| `spring-api/src/main/java/eu/royalblackwater/api/masterdata/` | Seed catalog, idempotent synchronization, local overrides, and administrative master-data maintenance. Internal seed metadata is not an API contract. | `SeedCatalogTest`, `MasterDataQueryServiceTest`, PostgreSQL integration; for `UnrecognizedPropertyException`, inspect mapper boundary. |
| `spring-api/src/main/java/eu/royalblackwater/api/onboarding/` | Structured newcomer guide with pages, blocks, and safe resources. | `NewcomerGuideService` and frontend draft tests; inspect ordering and embed validation. |
| `spring-api/src/main/java/eu/royalblackwater/api/operations/` | Unprivileged API for backup/update requests through controlled inbox files. Executes no host commands. | `ControlFileStore`, operations integration, and systemd runners; inspect status file, request ID, and file permissions. |
| `spring-api/src/main/java/eu/royalblackwater/api/persistence/` | Shared JDBC access, null parameters, and safe type conversion. Do not collect domain-specific queries here. | `JdbcQueryService`, `RowValues`, `SqlParameters`; normalize JDBC/Java types at the boundary. |
| `spring-api/src/main/java/eu/royalblackwater/api/privacy/` | Cookie consent, contact inbox, data export, data-subject requests, pseudonymization, and retention. No IP/user-agent collection in the contact workflow. | `CookieConsentServiceTest`, `PrivacyServiceTest`, `PrivacyIntegrationTest`, [retention](../reference/DATA_RETENTION.md); never print consent keys. |
| `spring-api/src/main/java/eu/royalblackwater/api/raidhelper/` | Profiles, targets, templates, payload rendering, and delayed external delivery. Failures must not block the calendar flow uncontrollably. | `RaidHelperDeliveryWorker`, probe/policy services, and [integration reference](../reference/RAID_HELPER_CALENDAR.md). |
| `spring-api/src/main/java/eu/royalblackwater/api/security/` | Authenticated principal, session filter, CSRF, password/secret cryptography, host/origin boundary, and the moderator-or-higher shared-content mutation boundary. Ordinary users retain read access and explicit profile/application/self-service writes; fleet/squad services apply the same staff threshold to management reads. | Security unit tests and `ApplicationIntegrationTest`; diagnose 401, role-based 403, CSRF 403, and request-boundary 403 separately. |
| `spring-api/src/main/java/eu/royalblackwater/api/securityops/` | Purpose-bound aggregate block signals, IP blocks, and security dashboard. No general request history. | `SecurityDashboardServiceTest`, [retention](../reference/DATA_RETENTION.md); read JDBC `DATE` through `RowValues`. |
| `spring-api/src/main/java/eu/royalblackwater/api/shared/` | Narrow cross-module web, filter, and mapping helpers without business logic. | `ApiControllerSupport`, `ListFilter`; add helpers only for multiple genuine consumers and without business logic. |
| `spring-api/src/main/java/eu/royalblackwater/api/ships/` | Read-only ship catalog, weapon classes, mounts, and performance profiles. Mutations go through master data. | `ShipQueryService`, list filters, and master-data seed tests; inspect taxonomy IDs and active records. |
| `spring-api/src/main/java/eu/royalblackwater/api/squads/` | Squads within a fleet, roster, roles, leadership, and memberships based on valid fleet memberships. | `SquadAccessPolicyTest` and PostgreSQL HTTP test; inspect fleet membership, membership status, and role capability together. |
| `spring-api/src/main/java/eu/royalblackwater/api/strategies/` | Two-layer Port-Battle strategy documents, ship-compatible website build references, ownership, and explicit public sharing. | `StrategyServiceTest`, shared-route security, overlay and build/ship validation, and background-file publication. |
| `spring-api/src/main/java/eu/royalblackwater/api/warehouse/` | Administrator-managed, fleet-scoped guild stock with member-linked or custom holders, reservation state, optimistic concurrency, and audit-backed notifications. Discord remains a downstream subscriber rather than a persistence dependency. | `WarehouseServiceTest`, warehouse HTTP lifecycle integration, migration V12, and [warehouse reference](../reference/GUILD_WAREHOUSE.md); inspect holder membership and row version on 400/409 responses. |
| `spring-api/src/main/java/eu/royalblackwater/api/webhooks/` | Website webhooks, event catalog, policy, delivery history, and concise outgoing notifications. Secrets remain encrypted. | Webhook policy/payload tests and delivery status; inspect target scope, event type, and redacted error. |

## Frontend feature modules

Feature modules live under `frontend/src/modules/`. Pages orchestrate, composables own
state and flows, API files own transport, and domain files own pure rules. A missing UI
guard is a UX defect; real permissions are decided exclusively by the backend.

| Module | Responsibility | Diagnostics and tests |
| --- | --- | --- |
| `frontend/src/modules/accounts/` | Login, registration, profile, preferences, and privacy self-service. | Session state, redirect, and `usePrivacySelfService`; browser smoke tests plus account-domain tests. |
| `frontend/src/modules/admin/` | Shared staff/admin workspace for users, logs, master data, privacy, webhooks, Raid Helper, and operations. | Isolate the affected composable instead of `AdminPage.vue`; inspect role visibility, page bindings, and API status. |
| `frontend/src/modules/builds/` | Build library, designer, calculation, search, print, and sharing. | Pure calculation/domain tests, contract fixtures, build, and browser; separate catalog loading from input changes. |
| `frontend/src/modules/calendar/` | Calendar view and event creation including explicit Raid Helper selection. | `calendarGrid` and page composables; inspect UTC/local date conversion and request payload. |
| `frontend/src/modules/combat/` | Local DPM/armor analysis based on the loaded catalog. | `combatDpm` unit tests; no API calls per input change. |
| `frontend/src/modules/files/` | File transport and shared client type rules. | Upload status, allowed types, and backend boundaries; the server remains authoritative. |
| `frontend/src/modules/fleet/` | Landing page, public fleet, and management workspace. | Backend-provided capabilities, filters, and responsive tests; do not infer roles from names. |
| `frontend/src/modules/forum/` | Thread list, creation, detail, replies, and owner actions. | Page composables, deletion confirmation, and attachment path. |
| `frontend/src/modules/groups/` | Group lists, own groups, creation, detail, and membership. | Test `groupDetail` rules and composable state separately. |
| `frontend/src/modules/guides/` | Guide search, editor, reader, table of contents, and print. | Presentation/discovery/print tests, Markdown sanitizing, and responsive reader styles. |
| `frontend/src/modules/legal/` | Public legal notice and admin editor. | Publish status, text presentation, and role visibility in all locales. |
| `frontend/src/modules/onboarding/` | Explorer-style newcomer workspace with home discovery, compact topic navigation, a wide Markdown/resource reader, and a focused two-pane maintainer editor over the same ordered hierarchy. | Inspect `NewcomerTopicExplorer`, `NewcomerFolderEditor`, composable selection/editing state, draft normalization, safe resolved resources, responsive styles, and the browser read/edit/save flow. |
| `frontend/src/modules/privacy/` | Privacy center and cookie banner; without a saved decision it does not open automatically while no optional integration is active. | `cookieConsentVisibility.test.mjs` and browser smoke tests for retry, payload, and error state. |
| `frontend/src/modules/ships/` | Thin read-only API access to ship master data. | Inspect consumers in builds/combat; do not introduce a second catalog logic. |
| `frontend/src/modules/squads/` | Squad list, own squads, creation, detail, and roster management. | `squadManagement`, page composables, and fleet-membership IDs in the payload. |
| `frontend/src/modules/strategy-planner/` | SVG strategy editing over preserved chart images, with separate creation, selected-property, transform, and sharing controls. Versioned overlay documents and pure geometry rules keep arrows/formations legible across scale, distinguish ovals from true circles, and preserve legacy plans. | `strategyPlanner.test.mjs`, document migration and geometry rules, page-model boundaries, responsive/letterboxed canvas coordinates, SVG export, and browser create/transform/save flow. |
| `frontend/src/modules/warehouse/` | Administrator warehouse workspace with spreadsheet-style facets and totals, member/custom holder editing, reservation state, and conflict-safe mutations. | `warehouse.test.mjs`, warehouse browser lifecycle, `useWarehousePage`, and backend 409 handling. |

The shared frontend areas `frontend/src/assets/`, `frontend/src/config/`,
`frontend/src/core/`, `frontend/src/locales/`, `frontend/src/router/`,
`frontend/src/shared/`, and `frontend/src/styles/` are not business modules. They own
only assets, runtime configuration, app shell, translations, routing, reusable building
blocks, and the global CSS cascade respectively. Changes there are cross-cutting and
require at least the frontend gate; routing/security changes also require matching backend tests.

## Infrastructure modules

Directories under `infrastructure/scripts/` are separated by lifecycle rather than file type.
Public root orchestrators remain `deploy.sh` and `update.sh`; production diagnostics begin
with the diagnostics module.

| Module | Responsibility and safe diagnostic entry point |
| --- | --- |
| `infrastructure/scripts/backup/` | Consistent PostgreSQL/file backups, retention, and manifests; verify with recovery contract tests. |
| `infrastructure/scripts/checks/` | Target-side readiness/doctor checks without repair through data deletion. |
| `infrastructure/scripts/deployment/` | Target-side installation and activation of versioned artifacts. Preserve failed-activation diagnostics first. |
| `infrastructure/scripts/diagnostics/` | Bounded remote collector and local redaction; use the [debugging runbook](../debugging/MODULE_DEBUGGING.md). |
| `infrastructure/scripts/generation/` | Deterministic generators for API, Java, seed/build catalogs, and reference docs; always validate with `--check`. |
| `infrastructure/scripts/lib/` | Reusable shell helpers and host modules; test callers, idempotency, and exit codes together. |
| `infrastructure/scripts/migration/` | Controlled legacy/data migrations outside immutable Flyway files. |
| `infrastructure/scripts/quality/` | Canonical repository, security, documentation, and full gates; agent scripts delegate only here. |
| `infrastructure/scripts/release/` | Artifact build, transfer, verification, rollback, and origin deployment. Never include production data in the artifact. |
| `infrastructure/scripts/services/` | Root-owned target runners for controlled inbox actions and service lifecycle. |
| `infrastructure/scripts/setup/` | Interactive first run and host composition; keep repeatable and fail-closed. |
| `infrastructure/scripts/tls/` | Certificate provisioning and renewal; never read private keys into diagnostics or the repository. |

## Complete a module change fully

1. Read the primary contract, callers, persistence, configuration, and the module row in this catalog.
2. Change behavior at the responsible boundary and add focused success, failure, and permission tests.
3. Update the diagnostic path so failures remain locatable without payloads or secrets.
4. For a new/renamed module, update docs and the agent cache and run
   `bash .agents/scripts/check-cache.sh`.
5. Run affected gates and, for a cross-cutting change, `make validate`.
