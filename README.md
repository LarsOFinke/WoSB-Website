# Iron Crown Fleet Hub

Fullstack prototype foundation for the Iron Crown Fleet Hub: builds, guides, forum, group search, fleet calendar, fleet management and staff operations.

```text
backend/   FastAPI + SQLAlchemy + SQLite dev database + cookie sessions
frontend/  Vue 3 + Vite + localized enterprise app shell
/docs      architecture, operations and production-readiness notes
```

## Current modules

- Build Manager with ship catalog, option catalog and user-owned builds.
- Guides with inline uploads and inline build references.
- Forum with upload placement in posts.
- Gruppensuche for fleet activity listings.
- Fleet calendar with staff-only event creation.
- Fleet management with applications, fleet leadership roles and profile synchronization.
- Staff panel for moderation and operational tasks.
- Locales for EN, DE, FR, ES, PT, RU and CN with strict coverage checks.

## Local start

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
wosb-seed --reset
wosb-dev
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Seeded development admin:

```text
admin / admin123
```

Change this before deployment through `backend/.env.example` settings.

## Important URLs

Backend:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/auth/me
http://127.0.0.1:8000/api/builds
http://127.0.0.1:8000/api/guides
http://127.0.0.1:8000/api/forum/threads
http://127.0.0.1:8000/api/groups
http://127.0.0.1:8000/api/calendar/events
http://127.0.0.1:8000/api/fleets
http://127.0.0.1:8000/api/admin/builds
```

Frontend:

```text
http://127.0.0.1:5173/home
http://127.0.0.1:5173/builds
http://127.0.0.1:5173/guides
http://127.0.0.1:5173/groups
http://127.0.0.1:5173/calendar
http://127.0.0.1:5173/forum
http://127.0.0.1:5173/fleets
http://127.0.0.1:5173/profile
http://127.0.0.1:5173/admin
```

## Production-foundation update

This pass focused on making the repository a cleaner base for production-grade iteration:

- documented the full current project inventory;
- added a rebuild plan and production checklist;
- added centralized backend logging and request IDs;
- split the frontend app shell into topbar/sidebar/composable/navigation modules;
- added enum/range database constraints for fresh schemas;
- fixed group computed properties for active count, spots left and joinability;
- consolidated docs around architecture, frontend, backend and operations;
- kept existing features and locale checks intact.

Start with [`docs/README.md`](docs/README.md) for the documentation index.

## Validation

Frontend:

```bash
cd frontend
npm run check:locales
npm run build
npm audit --omit=dev
find src -name '*.js' -print0 | xargs -0 -n1 node --check
```

Backend:

```bash
python -m compileall -q backend/src
```

## Production caveats

This repository is now a much cleaner prototype foundation, but before real users it still needs Alembic migrations, PostgreSQL staging/production configuration, rate limiting, automated tests, CI gates, durable file storage and proper secrets/session configuration. See [`docs/PRODUCTION_CHECKLIST.md`](docs/PRODUCTION_CHECKLIST.md).


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.


## Single Fleet Refactor

Der Flottenbereich arbeitet jetzt mit genau einer offiziellen Iron Crown Fleet. Registrierung, Profil und Flottenverwaltung referenzieren dieselbe zentrale Membership. Details stehen in `docs/SINGLE_FLEET_REFACTOR.md`.

## Build Designer Accuracy

The Build Designer now uses a complete ship-stat catalog, normalized upgrade effects and a visible base/modifier/effective stat breakdown. See `docs/BUILD_DESIGNER_ACCURACY.md`.
