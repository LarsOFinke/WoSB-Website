# Agent Onboarding – Royal Blackwater Fleet

This file is the token-efficient entry point for new repository agents. It does
not replace `AGENTS.md` or primary technical sources. Its purpose is to avoid
rediscovering established architecture and debugging fundamentals for every task.

## Start in under a minute

```bash
# 1. Print the current state without secrets
bash .agents/scripts/project-context.sh

# 2. Read the maintained system map
sed -n '1,260p' .agents/PROJECT_CACHE.md

# 3. Open the affected module and, for failures, the debugging cache
sed -n '1,260p' .agents/MODULE_CACHE.md
sed -n '1,220p' .agents/DEBUGGING_CACHE.md

# 4. Determine the appropriate gates after the change
bash .agents/scripts/check-changes.sh
```

Then read only the primary files affected by the task, their direct callers,
tests, configuration, and documentation. Do not start a blanket full-text
analysis of the entire repository when the cache already identifies the entry point.

For an explicitly broad quality and structure cleanup, follow the token-efficient
workflow in [REPOSITORY_SPRING_CLEANING.md](REPOSITORY_SPRING_CLEANING.md).

## Fixed system boundaries

- Runtime: `Browser -> NGINX -> Spring Boot -> PostgreSQL`.
- `spring-api/` is the only backend; do not reconstruct a Python web backend.
- Frontend: a page orchestrates, a composable owns flow/state, an API module makes
  network requests, and a domain module contains pure rules.
- Backend: OpenAPI specification -> generated API DTO -> module controller ->
  service -> repository -> PostgreSQL. Controllers own Spring MVC bindings and
  validate DTOs directly; mappers translate only between API/module DTOs,
  entities, and repository rows. Business logic, authorization, and transactions
  belong in the service; controllers and public service boundaries know neither
  entities nor JDBC rows/raw maps.
- Schema changes only through new Flyway migrations; never edit published
  migrations. Hibernate remains set to `validate`.
- Deployment and update start at the origin through `deploy.sh`/`update.sh` and
  use artifacts, backups, Flyway, and rollback. **Test is always the default
  target**; production may only be addressed with `--production`. Profiles are
  separated into `.env.origin.test` and `.env.origin.production`. Never delete
  production data or Docker volumes as a diagnostic measure.
- Diagnostics start at the origin through `infrastructure/scripts/diagnostics/debug.sh`
  and follow the same target selection: test without a flag, production with
  `--production`. Collection is bounded remotely and redacted locally; do not
  create raw logs or diagnostic archives on the target.
- Do not read, print, or version local `.env` files, private keys, tokens, personal
  data, or full IP addresses unless they are strictly required for the specific task.

## Direct entry points by task type

| Task | Primary entry point |
| --- | --- |
| Production failure | `infrastructure/scripts/diagnostics/debug.sh`, then `docs/debugging/DEPLOYMENT_INCIDENTS.md` |
| Local module failure | `.agents/DEBUGGING_CACHE.md`, `docs/debugging/MODULE_DEBUGGING.md` |
| Module responsibility | `.agents/MODULE_CACHE.md`, then `docs/architecture/MODULE_CATALOG.md` |
| Deployment/SSH | `docs/deployment/DEPLOYMENT.md`, `infrastructure/scripts/release/deploy-from-origin.sh` |
| Update/backup/DB preservation | `docs/debugging/2026-08-04-update-path-review.md` |
| Recovery | `docs/deployment/DISASTER_RECOVERY.md`, `tests/recovery/` |
| Backend domain | `spring-api/src/main/java/eu/royalblackwater/api/<domain>/` |
| API specification | `openapi/source/`, then composed `openapi/openapi.json`, `api/dto/*`, and the owning module controller |
| API usage/endpoints | `docs/reference/API.md`, `docs/reference/API_ENDPOINTS.md` |
| Tests and gates | `docs/development/TESTING.md`, `Makefile`, `infrastructure/scripts/quality/validate.sh` |
| Versioning/release class | `docs/development/VERSIONING.md`, `.agents/scripts/next-version.sh` |
| Frontend feature | `frontend/src/modules/<feature>/` |
| CSS/UI | `docs/reference/CSS_ARCHITECTURE.md`, affected module styles |
| Security | `SecurityConfiguration`, `security/`, `infrastructure/scripts/quality/security_audit.py` |
| Privacy | `privacy/`, `docs/reference/DATA_RETENTION.md` |

Script ownership: only the public orchestrators `deploy.sh` and `update.sh` live in
the repository root. All shared script logic is modularized under
`infrastructure/scripts/`: `quality/` for gates and audits, `generation/` for
generators, `release/` for packaging/deployment, plus domain-specific runtime
modules. The release artifact uses an explicit runtime allowlist; `quality/` and
`generation/` are not shipped to the target. Module-bound helpers under
`.agents/scripts/` and `frontend/scripts/` remain with their owners.

Use `rg` or `rg --files` first for file searches. Do not edit generated API DTOs or
locale output by hand; controller routes are module code and are audited against OpenAPI.

## Known stable state

- Version: read it from `VERSION`; do not copy a number from this document.
- Determine the next version token-efficiently with `bash .agents/scripts/next-version.sh
  patch|minor|major`: patch for fixes, minor for compatible features, major for
  incompatible or explicitly large extensions.
- The interactive first run is `./deploy.sh --configure`. It can set up the dedicated
  `rbfadmin` account and key through a one-time VPS bootstrap account and then deploy
  in the same run.
- Subsequent deployments use the configured key and `sudo -n`; the private bootstrap
  account is not persisted.
- Central API failures appear as `api_error`; authentication and authorization
  rejections as `security_401` and `security_403`. Do not add payloads or secrets to logs.
- `ApplicationIntegrationTest` tests the running Spring application over real HTTP
  against PostgreSQL/Testcontainers. Browser contracts live under
  `frontend/tests/browser/` and mock only `/api/` requests.
- Executable Java and frontend JavaScript files are limited to 420 lines. Only the
  documented declarative locale catalogs are exempt.
- Cookie settings do not open automatically without an existing decision while no
  optional cookie/tracking integration is active. Manual entry remains available
  through the footer and privacy center.
- Existing databases retain the unchanged Flyway V1 history; new databases start
  through B2 and the modular V3–V7 files. New changes from V8 onward are added as
  small domain-specific forward migrations.

## Verification without researching gates again

```bash
# Show recommendation only
bash .agents/scripts/check-changes.sh

# Run recommendation
bash .agents/scripts/check-changes.sh --run

# Complete gate for cross-cutting changes
bash .agents/scripts/check-all.sh
```

The scope helper delegates to existing repository gates. Frontend tests use
`bash .agents/scripts/check-frontend.sh`, which creates a missing local `.env`
temporarily from `.env.example` and guarantees its removal. The gate includes
Chromium browser smoke tests; install the browser locally once with
`cd frontend && npx playwright install chromium`.

The agent gates are intentionally token-efficient: on success they print only a
status line, and on failure a bounded log excerpt. Full tool output can be enabled
when needed with `AGENT_GATE_VERBOSE=1`. Direct entry points are:

```bash
bash .agents/scripts/check-backend.sh
bash .agents/scripts/check-frontend.sh
bash .agents/scripts/check-infrastructure.sh
bash .agents/scripts/check-docs.sh
bash .agents/scripts/check-cache.sh
bash .agents/scripts/check-all.sh
```

Let long-running commands continue in their existing process session. Do not waste
tokens through tight polling or repeated full output; instead wait for completion
or an actionable failure message and continue with that result. Do not restart a
still-running process merely because no new output has appeared.

Local, functionally complete changes may be committed as small traceable units when
explicitly requested. Commit and push remain two separate decisions: batch pushes
deliberately and perform them only when explicitly requested, because a push to
`main` starts external CI including the expensive NVD dependency check. A local
commit does not require an immediate push.

## Updating the cache

Update `PROJECT_CACHE.md` and this file in the same task when runtime topology,
deployment/recovery flow, binding gates, or central entry points change. New or
renamed modules additionally require updates to `MODULE_CACHE.md` and
`docs/architecture/MODULE_CATALOG.md`; reproduced, persistently useful root causes
require updates to `DEBUGGING_CACHE.md` and the appropriate runbook.
`check-cache.sh` verifies inventory completeness. Ephemeral facts such as branch,
revision, file count, or test count stay out of the text cache and are obtained live
through `project-context.sh`.
