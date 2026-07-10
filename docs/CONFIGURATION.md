# Configuration model

The project now separates **environment values** from **repository configuration**.

## Backend

Backend startup is intentionally fail-fast:

- `backend/.env` must exist, or `BLACKWATER_ENV_FILE` must point to another env file.
- `backend/config/app.toml` must exist, or `BLACKWATER_CONFIG_FILE` must point to another config file.

`WOSB_ENV_FILE` and `WOSB_CONFIG_FILE` remain compatibility aliases for older deployments.
- No unsafe runtime defaults are used for database, upload paths, CORS or seeded admin credentials.

### Environment values

Use `backend/.env.example` for local development and `backend/.env.production.example` for the Pi/Linux deployment baseline. Environment-specific or sensitive values belong in the resulting `backend/.env` file.

Production example:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://blackwater:<secret>@postgres:5432/blackwater
DB_SCHEMA_MODE=migrate
UPLOAD_DIR=/data/uploads
CORS_ORIGINS=https://your-domain.example
SESSION_COOKIE_SECURE=true
AUTO_SEED=true
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_PASSWORD=<long-random-password>
SEED_ADMIN_DISPLAY_NAME=Blackwater Command
```

`SEED_ADMIN_PASSWORD` must be changed before startup. Known placeholder/default passwords are rejected.


### Storage source of truth

There is no repository root `storage/` directory anymore. For local backend runs, use `DATABASE_URL=sqlite:///./storage/blackwater-hub.db` and `UPLOAD_DIR=storage/uploads`; relative runtime paths are resolved against `backend/`, independent of the shell working directory. For container deployments, the upload volume is mounted at `/data/uploads`.

Only `UPLOAD_DIR` decides the runtime upload location. The committed demo media remains under `backend/storage/uploads/demo`.

### Repo config

Use `backend/config/app.toml` for safe, non-secret settings that should travel with the repository:

- app name/version/API prefix
- logging behaviour
- cookie name/same-site/TTL
- upload size limits

## Frontend

`frontend/.env` is required before `npm run dev`, `npm run build` or `npm run preview`.

```env
VITE_API_BASE_URL=/api
```

The Vite dev-server settings live in `frontend/config/dev-server.json`. This keeps build-time env small while allowing the development proxy to remain versioned with the repo.

## Why this split?

- Secrets and deployment paths stay out of Git.
- Stable product configuration remains reviewable in Git.
- Missing config fails at startup/build time instead of silently using prototype defaults.


Database lifecycle details are documented in [DATABASE_MODES.md](DATABASE_MODES.md).
