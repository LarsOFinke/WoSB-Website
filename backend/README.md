# Backend

FastAPI backend for Royal Blackwater Vanguards.

## Mandatory configuration

The backend refuses to start without an env file.

```bash
cp .env.example .env
nano .env
```

Runtime/deployment values are in `.env`. Safe repository settings are in `config/app.toml`. For a manual PostgreSQL deployment, install `.[postgres]` and start from `.env.production.example`. The integrated Pi stack handles both automatically.

Required `.env` values:

```env
APP_ENV=development
DATABASE_URL=sqlite:///./storage/rbv-hub.db
DB_SCHEMA_MODE=create
UPLOAD_DIR=storage/uploads  # when running commands from backend/
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SESSION_COOKIE_SECURE=false
AUTO_SEED=true
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_PASSWORD=<strong-non-default-password>
SEED_ADMIN_DISPLAY_NAME=Community Admin
```

`SEED_ADMIN_PASSWORD` must not be a placeholder/default value.

## Start

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# or: . .venv/bin/activate
pip install -e .[dev]
rbv-seed --reset
rbv-dev
```

The legacy `wosb-seed` and `wosb-dev` entry points remain available as compatibility aliases.

API health check:

```text
http://127.0.0.1:8000/api/health
```

## Access policy

Public API reads are limited to the fleet portal, build catalog/details, ship/build option catalogs, authentication and health/home endpoints. Guides, groups, forum, calendar, profile and fleet-management operations require an authenticated user. Admin and staff mutations use the corresponding staff/admin dependency.

The backend is the authorization source of truth; frontend route guards only improve navigation and redirect behavior.

## Layout

```text
src/app
├── api              router composition and infrastructure endpoints
├── cli              command-line entry points
├── core             config, security, constants, logging, middleware, errors
├── db               SQLAlchemy session and schema lifecycle
├── seeds            deterministic catalog/demo data
└── modules          feature modules
    ├── accounts
    ├── admin
    ├── builds
    ├── calendar
    ├── content
    ├── files
    ├── fleet
    ├── forum
    ├── groups
    ├── guides
    └── ships
```

For the detailed module rules, see `../docs/MODULE_STRUCTURE.md`.

## Configuration split

- `core/config.py` loads `backend/.env` or `RBV_ENV_FILE`.
- `WOSB_ENV_FILE` remains a compatibility alias.
- `config/app.toml` contains non-secret application config.
- Process environment variables can override values from `.env`, but the env file still has to exist.

See `../docs/CONFIGURATION.md`.

## Logging

Logging is configured centrally in `app.core.logging`.

- Console logging is disabled by repo config unless explicitly enabled in `config/app.toml`.
- Request/application logs are persisted to `app_logs` and shown in the Admin Dashboard.
- Every response includes `X-Request-ID`.
- IP, forwarded IP, user-agent and query string are captured for operational diagnostics.

Do not log passwords, raw session tokens or file contents.

## Data model

The schema is normalized around users/profiles/fleet memberships, builds/build slots/build effects, guides/build references/files, forum attachments and group memberships. See `../docs/DATABASE_SCHEMA.md` and `../docs/BACKEND_ARCHITECTURE.md`.

## Pi deployment

Use `../docs/FIRST_RUN.md` and `../infrastructure/README.md`. Production runs PostgreSQL through Alembic; local development remains SQLite-based.


## Structure cleanup

- Backend feature code is organized under `src/app/modules/<domain>`; each concrete class stays one-class-per-file.
- `routes/__init__.py` files only re-export routers; implementation lives in `routes/router.py` or smaller route files.
- The repository has a single local upload tree at `backend/storage/uploads`; root-level `storage/` is intentionally removed. Runtime storage is configured through `UPLOAD_DIR`.
