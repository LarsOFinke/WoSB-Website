# Backend Architecture

The backend is now organized around a modular feature structure instead of large global `models`, `schemas` and `services` directories. The goal is to keep the codebase readable as the product grows while preserving KISS boundaries: HTTP, business rules, persistence and cross-cutting infrastructure are separated, but not over-abstracted.

## Top-level layers

```text
backend/
├── config/      non-secret repository configuration
├── storage/     repository demo upload assets; runtime location comes from `UPLOAD_DIR`
└── src/app/
    ├── api/     API router assembly and infrastructure endpoints
    ├── cli/     command-line entry points
    ├── core/    cross-cutting infrastructure
    ├── db/      SQLAlchemy engine/session and schema lifecycle
    ├── seeds/   deterministic catalog/demo seed data
    └── modules/ feature modules
```

Global `app/models`, `app/schemas` and `app/services` packages were removed during the cleanup. New code imports from `app.modules.<domain>...` directly.

## API layer

`app/api/router.py` is the single router composition point. It imports routers from feature modules and includes them on the shared API router.

Infrastructure endpoints that are not feature-owned, such as health checks, live in `app/api`.

Routes should only handle:

- HTTP method/path definitions.
- Dependency injection for DB/session/current user.
- Converting service errors into HTTP errors.
- Request and response schemas.

## Feature modules

Feature code lives under `backend/src/app/modules/<domain>`.

Each module can contain:

```text
models/    SQLAlchemy classes and persistence constants
schemas/   Pydantic request/response contracts
services/  business logic and validation
routes/    FastAPI route handlers
```

Current modules:

| Module | Responsibility |
| --- | --- |
| `accounts` | Auth, registration approval flow, profiles and sessions |
| `admin` | Admin dashboard, access review and log views |
| `builds` | Build designer, catalog options and stat calculation |
| `calendar` | Fleet calendar events |
| `content` | Shared inline embed parsing/rendering helpers |
| `files` | Upload validation and stored file metadata |
| `fleet` | Single official fleet, memberships and member directory |
| `forum` | Threads, posts and forum attachments |
| `groups` | Gruppensuche listings and signups |
| `guides` | Guides, guide attachments and build references |
| `ships` | Ship catalog endpoints and schemas |

## Authentication and access boundaries

Route access is declared with shared dependencies from `app.core.dependencies`:

- public: health/home, registration/login/session lookup, fleet portal reads, build catalog/details/options and ship catalog reads;
- authenticated: profile, guides, groups, forum, fleet calendar reads, fleet applications/management, personal builds and build creation;
- staff/admin: staff dashboard, registration approval, calendar mutation and privileged fleet operations.

Frontend route metadata mirrors this policy, but FastAPI remains the security boundary. New private modules must use `require_user`, `require_staff` or `require_admin` before invoking their service layer.

## Services

Services own business logic such as:

- Build validation and stat calculation.
- Fleet application and membership approval flows.
- Guide/forum embed validation.
- Upload validation.
- Calendar permissions.
- Group signup validation.

Services should be callable from route handlers, seeds and future tests without HTTP request objects.

## Models

Every concrete ORM class lives in its own file inside the owning module. Examples:

```text
modules/fleet/models/fleet.py
modules/fleet/models/fleet_membership.py
modules/builds/models/build.py
modules/builds/models/build_slot.py
```

Do not add global model packages. Concrete ORM classes belong to the owning module under `app/modules/<domain>/models`.

## Schemas

Every concrete Pydantic schema class lives in its own file inside the owning module. `schemas/__init__.py` may re-export public contracts; duplicated constants belong in `schemas/constants.py`.

Do not leak SQLAlchemy models directly to frontend code.

## Core

`core` contains cross-cutting infrastructure:

- `config.py`: strict env + repo config loader; requires `backend/.env` and `backend/config/app.toml`.
- `security.py`: password/session token helpers.
- `dependencies.py`: auth dependencies.
- `constants.py`: stable enum-like constants.
- `logging.py`: central log configuration.
- `middleware.py`: request logging/request IDs.
- `errors.py`: shared application error response shape.

## Seeds

Seed data now lives in top-level `app/seeds`, not inside `db`. This makes the responsibility clearer:

- `db` owns engine/session/schema lifecycle.
- `seeds` owns deterministic catalog and demo data.

## Logging

Application logging is configured once in `app.core.logging.configure_logging()`. Request logging is handled by `RequestLoggingMiddleware` and returns `X-Request-ID` on every response.

Logging configuration lives in `backend/config/app.toml`; deployment-specific runtime values live in `backend/.env`. The app does not silently fall back to prototype env defaults.

Use module loggers in new code:

```python
import logging

logger = logging.getLogger(__name__)
```

Do not log passwords, raw session tokens or uploaded file contents.

## Model registry

`app/modules/registry.py` imports all ORM model modules before schema creation/reset. This keeps SQLAlchemy metadata registration explicit without making `db` depend on legacy compatibility packages.

## Database standards

- Every table has a single primary key except intentional one-to-one profile table `user_profiles`.
- Many-to-many/domain references use join tables.
- Repeated option effects are stored in `build_item_effects`, not JSON blobs.
- Guide build links are stored in `guide_build_references`.
- Uploaded file metadata is stored in `stored_files`; binary content is externalized.
- Check constraints protect enum/range fields on newly created schemas.

## Transaction standards

Current prototype services commit internally for simplicity. Future production work should move toward explicit unit-of-work boundaries per route/service command, especially when adding migrations and tests.

## File/class organization

- Every backend class has a dedicated module.
- New classes go into the owning feature module.
- Root aggregate packages are intentionally absent; do not recreate `app/models`, `app/schemas` or `app/services`.
- Shared constants should live in `core/constants.py` or a module-level constants file rather than being duplicated in class files.

## Upload storage source of truth

- Repository demo uploads live only under `backend/storage/uploads/demo`.
- Runtime upload location is configured exclusively through `UPLOAD_DIR` in `backend/.env`.
- Do not add a root-level `storage/` tree; `.gitignore` intentionally blocks it to avoid split upload sources.
