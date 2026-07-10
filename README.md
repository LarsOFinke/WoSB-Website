# Iron Crown Fleet Hub

Fullstack prototype foundation for the Iron Crown Fleet Hub: builds, guides, forum, group search, fleet calendar, fleet management and staff/admin operations.

```text
backend/     FastAPI + SQLAlchemy + strict env/config loading
frontend/    Vue 3 + Vite + localized enterprise app shell
docs/        architecture, configuration and deployment notes
deployment/  first Pi deployment templates
```

## Current modules

- Public fleet portal at `/` with registration/fleet application entry.
- Build Manager with ship catalog, weapon validation, mortar slot and special crew effects.
- Guides with inline uploads and inline build references.
- Forum with upload placement in posts.
- Gruppensuche with optional time windows, signups, ship selection and optional saved-build linking.
- Fleet calendar with staff-only event creation.
- Fleet management with applications, member directory and profile synchronization.
- Admin dashboard with registration approval queue and DB-backed request/application logs.
- Locales for EN, DE, FR, ES, PT, RU and CN with strict coverage checks.

## Configuration is mandatory

The project now fails fast when deployment config is missing.

Backend:

```bash
cd backend
cp .env.example .env
# edit .env before first start
```

Frontend:

```bash
cd frontend
cp .env.example .env
# VITE_API_BASE_URL=/api is correct for same-domain reverse proxy deployments
```

Non-sensitive backend settings live in `backend/config/app.toml`; frontend dev-server settings live in `frontend/config/dev-server.json`.

Read [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) before deploying.

## Local start

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# or: . .venv/bin/activate
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

The old `admin / admin123` prototype default is gone. Set `SEED_ADMIN_PASSWORD` in `backend/.env` to a strong non-default password before seeding.

## Important URLs

```text
http://127.0.0.1:5173/            # public fleet portal
http://127.0.0.1:5173/builds
http://127.0.0.1:5173/guides
http://127.0.0.1:5173/groups
http://127.0.0.1:5173/calendar
http://127.0.0.1:5173/forum
http://127.0.0.1:5173/fleets     # fleet management
http://127.0.0.1:5173/profile
http://127.0.0.1:5173/admin
```

## Raspberry Pi first deployment

Start with [`docs/PI_DEPLOYMENT.md`](docs/PI_DEPLOYMENT.md). Templates are in `deployment/pi/`:

- `iron-crown-api.service`
- `nginx.conf.example`

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

This is suitable as a first Pi deployment foundation. For real public production, still add Alembic migrations, PostgreSQL, CI tests, rate limiting, backups, durable upload storage and hardened HTTPS/cookie/session operations. See [`docs/PRODUCTION_CHECKLIST.md`](docs/PRODUCTION_CHECKLIST.md) and [`docs/MODULE_STRUCTURE.md`](docs/MODULE_STRUCTURE.md).


## Structure cleanup

- Backend feature code is organized under `backend/src/app/modules/<domain>`; each concrete class stays one-class-per-file.
- FastAPI app creation lives in `app/core/app_factory.py`; route implementations live in module-local `routes/router.py` files.
- Global aggregate packages such as `app/models`, `app/schemas` and `app/services` are intentionally removed.
- The repository has a single local upload tree at `backend/storage/uploads`; root-level `storage/` is intentionally removed. Runtime storage is configured through `UPLOAD_DIR`.

See [`docs/MODULE_STRUCTURE.md`](docs/MODULE_STRUCTURE.md) and [`docs/SPRING_CLEANUP.md`](docs/SPRING_CLEANUP.md).
