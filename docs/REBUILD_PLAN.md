# Rebuild Plan Toward Production Grade

The project was not rewritten by deleting all working features. Instead, this plan documents a controlled rebuild path and the concrete pass already applied.

## Guiding principles

- Keep business rules in services, not Vue pages or route handlers.
- Keep routers thin: HTTP concerns in routes, domain decisions in services.
- Keep the database normalized first; denormalize only with a measured reason.
- Keep frontend API adapters thin and feature-scoped.
- Prefer small, replaceable modules over framework-heavy abstractions.
- Document every remaining prototype constraint instead of hiding it.

## Target architecture

```text
backend/src/app
├── api/routes          HTTP layer, auth dependencies, response models
├── core                config, security, constants, logging, middleware, errors
├── db                  SQLAlchemy session, initialization and seed orchestration
├── models              SQLAlchemy entities and relationships
├── schemas             Pydantic request/response DTOs
└── services            business logic and transactional operations

frontend/src
├── core                reusable shell/components/composables/navigation
├── locales             translations and locale runtime
├── pages               route-level screens
├── router              route table and auth guards
├── services            HTTP adapters and client utilities
└── styles              global design tokens and responsive rules
```

## Iteration 1: Document and stabilize

Completed:

- Added a full project inventory.
- Added a rebuild plan and production checklist.
- Added central logging configuration and request logging middleware.
- Added request IDs via `X-Request-ID`.
- Added explicit app environment/log settings.

## Iteration 2: Structure and reduce coupling

Completed:

- Split the large navigation component into `AppTopbar`, `AppSidebar`, `AppNavbar`, `useAppShell` and a navigation model.
- Moved sidebar state handling into a composable so visual components can stay focused on layout.
- Added backend constants/enums for roles and membership statuses to reduce scattered string literals.
- Added database-level check constraints for high-risk enum/range fields on new schemas.

## Iteration 3: Production-readiness pass

Completed:

- Added documentation for operations, backend architecture, frontend architecture and production checklist.
- Added request logging with duration, method, path and status code.
- Fixed `Group` computed properties so API output reflects active members, available spots and joinability.
- Kept existing feature behavior intact while preparing the project for migrations/testing.

## Next rebuild steps before real production

1. Add Alembic migrations and stop using `create_all` for production schema changes.
2. Move from SQLite to PostgreSQL in staging/production.
3. Add automated backend tests for auth, guides, forum, fleet membership and uploads.
4. Add frontend component tests for app shell, rich embeds and complex forms.
5. Add rate limiting on auth and upload endpoints.
6. Move uploads to object storage or durable shared storage.
7. Add CI gates: backend compile/tests, frontend locale check/build, linting and audit.
8. Add observability sinks for logs and error metrics.
