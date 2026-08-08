# Cached Quick Overview – Modules

This cache is the fast routing layer for agents. The authoritative functional source is
the [module catalog](../docs/architecture/MODULE_CATALOG.md), followed by the affected
source code. `bash .agents/scripts/check-cache.sh` ensures no module directory is missing
from docs or cache; it does not assess the factual accuracy of a description.

## Backend at a glance

| Path | Short responsibility | First checkpoint |
| --- | --- | --- |
| `spring-api/src/main/java/eu/royalblackwater/api/account/` | auth, session, profile, registration, admin seed | `AuthService`, bootstrap/HTTP tests |
| `spring-api/src/main/java/eu/royalblackwater/api/audit/` | data-minimized change audit | `AuditService`, entity/action/field list |
| `spring-api/src/main/java/eu/royalblackwater/api/builds/` | build persistence, validation, calculation, print | calculator/contract tests |
| `spring-api/src/main/java/eu/royalblackwater/api/calendar/` | calendar and events | ISO date binding, `CalendarService` |
| `spring-api/src/main/java/eu/royalblackwater/api/config/` | composition, properties, security, errors | `application.yml`, startup/binding failures |
| `spring-api/src/main/java/eu/royalblackwater/api/content/` | secure content embeds | validator plus callers |
| `spring-api/src/main/java/eu/royalblackwater/api/dto/` | generated HTTP DTOs | `openapi/source/` + assembler/DTO generator; never edit generated DTOs directly |
| `spring-api/src/main/java/eu/royalblackwater/api/core/` | health/readiness/core operations | health plus DB/Flyway |
| `spring-api/src/main/java/eu/royalblackwater/api/files/` | uploads, quotas, types, ownership | storage/path boundaries |
| `spring-api/src/main/java/eu/royalblackwater/api/fleet/` | fleet, memberships, roles/capabilities | AccessPolicy and bootstrap membership |
| `spring-api/src/main/java/eu/royalblackwater/api/forum/` | threads, posts, attachments | ownership/moderation |
| `spring-api/src/main/java/eu/royalblackwater/api/groups/` | groups and members | `GroupService` |
| `spring-api/src/main/java/eu/royalblackwater/api/guides/` | guides, references, Markdown | service plus print/sanitizing |
| `spring-api/src/main/java/eu/royalblackwater/api/legal/` | public/admin legal notice | publish status and properties |
| `spring-api/src/main/java/eu/royalblackwater/api/masterdata/` | seeds, overrides, master data | seeder/mapper/PostgreSQL tests |
| `spring-api/src/main/java/eu/royalblackwater/api/onboarding/` | newcomer guide | block ordering/embed validation |
| `spring-api/src/main/java/eu/royalblackwater/api/operations/` | backup/update inbox | control file and host runner |
| `spring-api/src/main/java/eu/royalblackwater/api/persistence/` | JDBC/type helpers | null parameters and `RowValues` |
| `spring-api/src/main/java/eu/royalblackwater/api/privacy/` | consent, export, requests, deletion/retention | `PrivacyIntegrationTest`, do not log keys |
| `spring-api/src/main/java/eu/royalblackwater/api/raidhelper/` | external event delivery | policy, worker, delivery status |
| `spring-api/src/main/java/eu/royalblackwater/api/security/` | session, CSRF, host/origin, cryptography | test 401/403/CSRF separately |
| `spring-api/src/main/java/eu/royalblackwater/api/securityops/` | block signals/IP blocks/dashboard | aggregation, `RowValues.date` |
| `spring-api/src/main/java/eu/royalblackwater/api/shared/` | shared web/filter/mapper helpers | no business logic, multiple consumers |
| `spring-api/src/main/java/eu/royalblackwater/api/ships/` | read-only ship catalog | query/filter/taxonomy |
| `spring-api/src/main/java/eu/royalblackwater/api/squads/` | squad/roster on fleet membership | fleet ID, status, capability |
| `spring-api/src/main/java/eu/royalblackwater/api/webhooks/` | webhook policy and delivery | scope/event/encrypted secret |

## Frontend at a glance

For every feature module: `page -> composable -> api/domain`; diagnose error state in
the composable, not in the page.

| Path | Short responsibility | First checkpoint |
| --- | --- | --- |
| `frontend/src/modules/accounts/` | login, registration, profile, privacy self-service | session/redirect/composable |
| `frontend/src/modules/admin/` | staff/admin workspaces | active sub-composable and role metadata |
| `frontend/src/modules/builds/` | library, designer, calculation, print | pure domain/contract tests |
| `frontend/src/modules/calendar/` | calendar/event creation | UTC payload and grid |
| `frontend/src/modules/combat/` | local DPM analysis | domain calculation without typing requests |
| `frontend/src/modules/files/` | file API and client types | upload status; backend remains authoritative |
| `frontend/src/modules/fleet/` | landing, public, management | backend capabilities/responsive behavior |
| `frontend/src/modules/forum/` | threads/posts | composable, ownership, confirmation |
| `frontend/src/modules/groups/` | group workflows | separate domain from state |
| `frontend/src/modules/guides/` | search, editor, reader, print | sanitizing/presentation/responsive behavior |
| `frontend/src/modules/legal/` | legal notice and editor | publish status/locale |
| `frontend/src/modules/onboarding/` | newcomer guide | draft/resource rules |
| `frontend/src/modules/privacy/` | privacy center/cookie banner | retry, payload, keep errors visible |
| `frontend/src/modules/ships/` | ship catalog transport | consumers in builds/combat |
| `frontend/src/modules/squads/` | lists, own squads, roster | membership ID/management rules |

Shared areas: `frontend/src/assets/`, `frontend/src/config/`, `frontend/src/core/`,
`frontend/src/locales/`, `frontend/src/router/`, `frontend/src/shared/`, and
`frontend/src/styles/`. Changes are usually cross-cutting; locale output and `dist/`
remain generated.

## Infrastructure at a glance

| Path | Short responsibility | Safe entry point |
| --- | --- | --- |
| `infrastructure/scripts/backup/` | backup and retention | backup/recovery contract |
| `infrastructure/scripts/checks/` | readiness/doctor | inspect read-only |
| `infrastructure/scripts/deployment/` | target installation/activation | preserve failed-activation log |
| `infrastructure/scripts/diagnostics/` | remote collection/local redaction | `debug.sh --help` |
| `infrastructure/scripts/generation/` | deterministic generators | respective `--check` |
| `infrastructure/scripts/lib/` | shared shell/host helpers | direct callers and exit codes |
| `infrastructure/scripts/migration/` | controlled legacy-data paths | inspect source/target/recovery first |
| `infrastructure/scripts/quality/` | canonical gates/audits | `make validate` |
| `infrastructure/scripts/release/` | build, transfer, verify, rollback | origin wrapper and artifact manifest |
| `infrastructure/scripts/services/` | root-owned runtime runners | inbox/status/systemd |
| `infrastructure/scripts/setup/` | first run | options → workflow → composition |
| `infrastructure/scripts/tls/` | certificates | metadata; never print private keys |

## Cache rule

Whenever a module is added, removed, or renamed, run:

```bash
bash .agents/scripts/check-cache.sh
bash .agents/scripts/check-docs.sh
```

The live snapshot from `bash .agents/scripts/project-context.sh` reports
`agent_cache_status=ok` or `stale`. A green inventory check does not replace the
functional maintenance of this summary and the module catalog.
